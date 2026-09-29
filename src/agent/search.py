"""Web search tool using Serper.dev.

Concept note — why a separate search module: the search provider is
swappable. If Serper's limits are insufficient, we can switch to another
provider by changing this one file.
"""

from __future__ import annotations

import httpx

from ..config import Config
from ..logging import get_logger

logger = get_logger(__name__)

SERPER_URL = "https://google.serper.dev/search"


def search(query: str, config: Config) -> list[dict]:
    """Search the web using Serper.dev.

    Returns a list of results with title, url, and snippet.
    """
    if not config.serper_api_key:
        logger.warning("SERPER_API_KEY not set, returning empty results")
        return []

    try:
        resp = httpx.post(
            SERPER_URL,
            headers={
                "X-API-KEY": config.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": 5},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("organic", [])
    except Exception as e:
        logger.error(f"search failed: {e}")
        return []
