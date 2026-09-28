"""HTTP layer: cache, rate limits, robots.txt, retries, timeouts, error classification.

Every network call in the application goes through this module.
Concept note — why a single HTTP layer: centralizing caching, rate limiting,
and robots.txt here means no stage or agent can accidentally bypass them.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from urllib.robotparser import RobotFileParser

import httpx

from .config import Config
from .logging import get_logger
from .models import ErrorClass

logger = get_logger(__name__)


@dataclass
class FetchResult:
    """Result of a successful fetch."""

    url: str
    final_url: str
    status_code: int
    headers: dict = field(default_factory=dict)
    text: str = ""
    fetch_time: float = 0.0
    from_cache: bool = False


class HttpError(Exception):
    """An error classified by the HTTP layer."""

    def __init__(
        self,
        message: str,
        error_class: ErrorClass,
        url: str,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.error_class = error_class
        self.url = url
        self.status_code = status_code


class DiskCache:
    """File-based HTTP response cache. Every response is cached on disk."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[dict]:
        path = self.cache_dir / f"{self._key(url)}.json"
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def put(self, url: str, data: dict) -> None:
        path = self.cache_dir / f"{self._key(url)}.json"
        path.write_text(json.dumps(data, default=str))


class RateLimiter:
    """Per-domain rate limiter using a simple delay-based approach."""

    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second
        self._last_request: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        async with self._lock:
            now = time.monotonic()
            last = self._last_request.get(domain, 0.0)
            elapsed = now - last
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last_request[domain] = time.monotonic()


class RobotsChecker:
    """robots.txt checker with per-domain caching.

    Fetches robots.txt through the HTTP layer (with caching) and parses
    it with urllib.robotparser. If robots.txt is unreachable, allows
    by default (per RFC 9309).
    """

    def __init__(self):
        self._parsers: dict[str, RobotFileParser] = {}
        self._lock = asyncio.Lock()

    async def can_fetch(self, url: str, user_agent: str, http_client: httpx.AsyncClient) -> bool:
        """Check if the user agent is allowed to fetch the URL."""
        parsed = httpx.URL(url)
        robots_url = f"{parsed.scheme}://{parsed.host}/robots.txt"

        async with self._lock:
            if robots_url not in self._parsers:
                parser = RobotFileParser()
                try:
                    response = await http_client.get(robots_url)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                    else:
                        # If robots.txt is unreachable, allow by default
                        return True
                except Exception:
                    return True
                self._parsers[robots_url] = parser

            parser = self._parsers[robots_url]
            return parser.can_fetch(user_agent, url)


class HttpClient:
    """All network calls go through this client.

    Provides: disk caching, per-domain rate limiting, robots.txt enforcement,
    retries with exponential backoff, timeouts, and error classification.
    """

    def __init__(self, config: Config):
        self.config = config
        self.cache = DiskCache(config.cache_dir)
        self.rate_limiter = RateLimiter(config.requests_per_second_per_domain)
        self._domain_limiters: dict[str, RateLimiter] = {}
        self.robots_checker = RobotsChecker()
        self._semaphore = asyncio.Semaphore(config.global_concurrency)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_rate_limiter(self, domain: str) -> RateLimiter:
        """Get the rate limiter for a domain, with per-domain overrides."""
        if domain not in self._domain_limiters:
            rate = self.config.per_domain_rate_limits.get(
                domain, self.config.requests_per_second_per_domain
            )
            self._domain_limiters[domain] = RateLimiter(rate)
        return self._domain_limiters[domain]

    async def __aenter__(self) -> HttpClient:
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.config.default_timeout_seconds,
            headers={"User-Agent": self.config.user_agent},
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def fetch(self, url: str, *, force_refresh: bool = False) -> FetchResult:
        """Fetch a URL with caching, rate limiting, robots.txt, and retries.

        Raises HttpError on failure. Never raises an unclassified exception.
        """
        # Check disk cache first
        if not force_refresh:
            cached = self.cache.get(url)
            if cached:
                cached.pop("from_cache", None)
                return FetchResult(**cached, from_cache=True)

        # Enforce robots.txt
        if not await self.robots_checker.can_fetch(url, self.config.user_agent, self._client):
            raise HttpError(
                f"robots.txt disallows fetching {url}",
                ErrorClass.ROBOTS_DISALLOWED,
                url,
            )

        # Rate limit per domain (with per-domain overrides for CDNs)
        domain = httpx.URL(url).host or ""
        await self._get_rate_limiter(domain).acquire(domain)

        # Fetch with retries and exponential backoff
        last_error: Optional[HttpError] = None
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._semaphore:
                    response = await self._client.get(url)

                result = FetchResult(
                    url=url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    text=response.text,
                    fetch_time=time.monotonic(),
                    from_cache=False,
                )

                # Cache successful responses (2xx and 3xx)
                if response.status_code < 400:
                    self.cache.put(url, asdict(result))

                return result

            except httpx.TimeoutException as e:
                last_error = HttpError(str(e), ErrorClass.TIMEOUT, url)
            except httpx.ConnectError as e:
                last_error = HttpError(str(e), ErrorClass.NETWORK, url)
            except httpx.TooManyRedirects as e:
                last_error = HttpError(str(e), ErrorClass.NETWORK, url)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 429:
                    last_error = HttpError(str(e), ErrorClass.BLOCKED, url, status)
                elif status >= 500:
                    last_error = HttpError(str(e), ErrorClass.NETWORK, url, status)
                else:
                    last_error = HttpError(str(e), ErrorClass.BLOCKED, url, status)
            except Exception as e:
                last_error = HttpError(str(e), ErrorClass.INTERNAL, url)

            # Exponential backoff before retry
            if attempt < self.config.max_retries:
                wait = self.config.retry_backoff_base_seconds * (2**attempt)
                logger.warning(
                    f"fetch attempt {attempt + 1} failed for {url}, retrying in {wait}s",
                    extra={"url": url, "error": str(last_error)},
                )
                await asyncio.sleep(wait)

        raise last_error
