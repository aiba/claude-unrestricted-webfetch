"""MCP server providing unrestricted web fetch via persistent headless Chrome.

Two tools:
  - fetch: returns full page content as markdown
  - fetch_extract: summarizes/extracts content using Claude Haiku
"""

import atexit

import html2text
import anthropic
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fetch")

_MAX_CONTENT_CHARS = 200_000
_EXTRACT_MAX_CHARS = 500_000
_JS_RENDER_WAIT_MS = 3_000

# Persistent browser — launched once, reused for all requests.
_pw = None
_browser = None


async def _get_browser():
    global _pw, _browser
    if _browser is None:
        stealth = Stealth()
        _pw = await stealth.use_async(async_playwright()).__aenter__()
        _browser = await _pw.chromium.launch(headless=True)
        atexit.register(_shutdown_sync)
    return _browser


def _shutdown_sync():
    """Best-effort cleanup at exit — browser process will die with server anyway."""
    pass


async def _fetch_url(url: str) -> str:
    """Fetch a URL with headless Chrome and return content as markdown."""
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(_JS_RENDER_WAIT_MS)
        html = await page.content()
    finally:
        await page.close()

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0  # no wrapping
    return converter.handle(html)


@mcp.tool()
async def fetch(url: str) -> str:
    """Fetch a URL and return its full content as markdown.

    Uses a persistent headless Chrome browser with stealth mode, so
    JavaScript-rendered pages work correctly. Content is truncated
    to 200k characters.
    """
    content = await _fetch_url(url)
    if len(content) > _MAX_CONTENT_CHARS:
        content = content[:_MAX_CONTENT_CHARS] + "\n\n[...truncated...]"
    return content


@mcp.tool()
async def fetch_extract(url: str, prompt: str) -> str:
    """Fetch a URL and extract/summarize specific information using a fast AI model.

    More token-efficient than fetch — use this when you only need specific
    information from a page rather than the full content.

    Args:
        url: The URL to fetch.
        prompt: What information to extract from the page.
    """
    content = await _fetch_url(url)
    if len(content) > _EXTRACT_MAX_CHARS:
        content = content[:_EXTRACT_MAX_CHARS] + "\n\n[...truncated...]"

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is the content of {url}:\n\n"
                    f"<content>\n{content}\n</content>\n\n"
                    f"{prompt}"
                ),
            }
        ],
    )
    return response.content[0].text


if __name__ == "__main__":
    mcp.run(transport="stdio")
