"""MCP server providing unrestricted web fetch tools.

Two tools:
  - fetch: returns full page content as markdown
  - fetch_extract: summarizes/extracts content using Claude Haiku
"""

import html2text
import anthropic
from curl_cffi import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fetch")

_LYNX_UA = "Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1"

_MAX_CONTENT_CHARS = 200_000
_EXTRACT_MAX_CHARS = 500_000


def _fetch_url(url: str) -> str:
    """Fetch a URL and return its content as markdown."""
    resp = requests.get(
        url,
        headers={"User-Agent": _LYNX_UA},
        allow_redirects=True,
        timeout=30,
    )
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")

    if "html" in content_type:
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.body_width = 0  # no wrapping
        return converter.handle(resp.text)
    else:
        return resp.text


@mcp.tool()
def fetch(url: str) -> str:
    """Fetch a URL and return its full content as markdown.

    Use this for reading web pages without restrictions.
    Content is truncated to 200k characters.
    """
    content = _fetch_url(url)
    if len(content) > _MAX_CONTENT_CHARS:
        content = content[:_MAX_CONTENT_CHARS] + "\n\n[...truncated...]"
    return content


@mcp.tool()
def fetch_extract(url: str, prompt: str) -> str:
    """Fetch a URL and extract/summarize specific information using a fast AI model.

    More token-efficient than fetch — use this when you only need specific
    information from a page rather than the full content.

    Args:
        url: The URL to fetch.
        prompt: What information to extract from the page.
    """
    content = _fetch_url(url)
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
