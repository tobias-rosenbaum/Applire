"""
Tiered job-description scraper.

Tier 1: httpx (plain HTTP fetch) + BeautifulSoup extraction.
Tier 2: Playwright headless Chromium for JS-rendered pages (StepStone, Indeed DACH).
Fallback: raises ScraperError with human-readable instructions.

Public API:
    scrape_job_url(url: str) -> str
    ScraperError
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

_MIN_TEXT_LENGTH = 200

_JS_HOSTS: frozenset[str] = frozenset(
    {
        "www.stepstone.de",
        "www.stepstone.at",
        "www.stepstone.ch",
        "de.indeed.com",
        "at.indeed.com",
        "ch.indeed.com",
    }
)


class ScraperError(Exception):
    """Raised when all tiers fail to extract job text."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(reason)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_url(url: str) -> None:
    """Raise ValueError if *url* is not a safe http(s) URL."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Only http and https URLs are supported, got scheme: {parsed.scheme!r}"
        )
    if not parsed.netloc:
        raise ValueError(f"Not a valid URL: {url!r}")


def _requires_js(url: str) -> bool:
    """Return True if *url* belongs to a known JS-rendered job board."""
    host = urlparse(url).hostname or ""
    return host in _JS_HOSTS


def _extract_text(html: str) -> str | None:
    """
    Extract the main job-description text from *html*.

    Strips scripts, styles, nav, header, and footer elements, then tries a
    priority list of candidate selectors.  Returns None if the result is
    shorter than _MIN_TEXT_LENGTH characters.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Priority list: most specific → least specific
    candidates = [
        soup.find(id=lambda v: v and "jobdescription" in v.lower()),
        soup.find(class_=lambda v: v and any(
            "job-description" in c.lower() or "jobdescription" in c.lower()
            for c in (v if isinstance(v, list) else [v])
        )),
        soup.find("article"),
        soup.find("main"),
        soup.find("body"),
    ]

    for node in candidates:
        if node is None:
            continue
        text = node.get_text(separator=" ", strip=True)
        if len(text) >= _MIN_TEXT_LENGTH:
            return text

    return None


async def _fetch_tier1(url: str) -> str | None:
    """Fetch *url* with httpx and extract text. Returns None on failure or thin content."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Apliqa/1.0)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
        return _extract_text(response.text)
    except Exception:
        return None


async def _fetch_tier2(url: str) -> str | None:
    """Render *url* with Playwright Chromium and extract text."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        try:
            await page.wait_for_selector(
                "article, main, [id*=jobDescription], [class*=job-description]",
                timeout=10_000,
            )
        except Exception:
            pass  # proceed with whatever is rendered
        html = await page.content()
        await browser.close()

    return _extract_text(html)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def scrape_job_url(url: str) -> str:
    """
    Return extracted job-description text for *url*.

    Raises:
        ValueError: if *url* is not a valid http(s) URL.
        ScraperError: if all tiers fail to extract usable text.
    """
    _validate_url(url)

    if not _requires_js(url):
        text = await _fetch_tier1(url)
        if text:
            return text

    try:
        text = await _fetch_tier2(url)
        if text:
            return text
    except ScraperError:
        raise
    except Exception as exc:
        raise ScraperError(url, f"JS render failed: {exc}") from exc

    raise ScraperError(
        url,
        "Could not extract job text from this page. "
        "Please paste the job description manually.",
    )
