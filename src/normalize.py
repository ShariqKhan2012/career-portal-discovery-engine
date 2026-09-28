"""URL normalization — handles the cases from master prompt Appendix B.

Concept note — why normalize: directory listings are human-maintained and
contain typos, Markdown artifacts, and tracking parameters. Normalization
deterministically cleans these before any further processing.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Parameters that carry no semantic meaning for careers pages
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_cid", "utm_reader", "utm_referrer",
    "utm_social", "utm_social-type", "utm_brand",
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid",
    "ref", "ref_url", "ref_src", "ref_campaign",
    "source", "medium", "campaign",
    "hubs_spot", "hubs_signup", "hubs_signup-cta",
}

# Regex to extract URL from broken Markdown like:
#   https://aulaatcoventry.notion.site/career](https://…)
#   [https://example.com](https://example.com)
_MARKDOWN_URL_RE = re.compile(r"https?://[^\s\[\]()<>\"']+")

# Trailing punctuation that is never part of a URL
_TRAILING_PUNCT = ",.;:!?)]}\"'"

# Known URL shorteners that need expansion
_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "buff.ly", "is.gd", "shorturl.com", "rebrand.ly",
}


def strip_trailing_punctuation(url: str) -> str:
    """Remove trailing punctuation that is never part of a URL.

    Handles: https://alley.co/careers/,  →  https://alley.co/careers/
             https://www.carmatec.com/careers/.  →  https://www.carmatec.com/careers/
             https://www.akamai.com/careers]]  →  https://www.akamai.com/careers
    """
    return url.rstrip(_TRAILING_PUNCT)


def repair_broken_markdown(url: str) -> str:
    """Extract the real URL from broken Markdown.

    Handles: https://aulaatcoventry.notion.site/career](https://…)
    The Markdown artifact is `](...)` appended to the URL.
    """
    match = _MARKDOWN_URL_RE.match(url)
    if match:
        return match.group(0)
    return url


def remove_tracking_params(url: str) -> str:
    """Remove tracking parameters from a URL.

    Handles: https://www.npmjs.com/jobs?utm_source=nodeweekly&utm_medium=email
    →       https://www.npmjs.com/jobs
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url
    params = parse_qs(parsed.query, keep_blank_values=False)
    clean = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
    new_query = urlencode(clean, doseq=True) if clean else ""
    return urlunparse(parsed._replace(query=new_query))


def upgrade_to_https(url: str) -> str:
    """Upgrade http:// to https:// where the URL uses http://.

    Handles: http://jobs.ably.io  →  https://jobs.ably.io
    """
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def is_shortener(url: str) -> bool:
    """Check if the URL uses a known shortener domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Strip www. prefix for comparison
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in _SHORTENER_DOMAINS


def normalize_url(url: str) -> str:
    """Apply all deterministic normalization steps in order.

    Steps: repair Markdown → strip punctuation → remove tracking → upgrade http.
    Shortener expansion is NOT done here (requires HTTP, handled separately).
    """
    if not url:
        return url
    url = repair_broken_markdown(url)
    url = strip_trailing_punctuation(url)
    url = remove_tracking_params(url)
    url = upgrade_to_https(url)
    return url
