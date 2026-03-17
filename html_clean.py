"""Shared HTML cleanup and markdown conversion for MCP fetch servers."""

import re

import html2text
from bs4 import BeautifulSoup, Comment

_STRIP_TAGS = [
    "script", "style", "nav", "header", "footer", "noscript",
    "svg", "iframe", "select", "option", "form", "input", "button",
    "link", "meta",
]
_STRIP_ROLES = ["navigation", "banner", "contentinfo", "complementary", "search"]


def _clean_url(url: str) -> str:
    """Extract real URL from tracking wrappers, drop long junk URLs."""
    if not url:
        return url
    # Amazon redirect URLs embed the real URL at the end
    m = re.search(r"(https://www\.amazon\.com/(?:dp|gp|s\?)[^\s&]*)", url)
    if m:
        return m.group(1).split("?")[0]
    if len(url) > 200:
        return ""
    return url


def clean_html(raw_html: str) -> str:
    """Strip boilerplate elements and tracking URLs from HTML."""
    soup = BeautifulSoup(raw_html, "lxml")

    for tag in _STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()
    for role in _STRIP_ROLES:
        for el in soup.find_all(attrs={"role": role}):
            el.decompose()
    for el in soup.find_all(attrs={"aria-hidden": "true"}):
        el.decompose()
    for el in soup.find_all(
        attrs={"style": lambda s: s and "display:none" in s.replace(" ", "")}
    ):
        el.decompose()
    for comment in soup.find_all(
        string=lambda text: isinstance(text, Comment)
    ):
        comment.extract()

    # Strip all attributes except cleaned hrefs
    for el in soup.find_all(True):
        href = el.get("href")
        el.attrs = {}
        if href and el.name == "a":
            cleaned = _clean_url(href)
            if cleaned:
                el["href"] = cleaned
            else:
                el.unwrap()

    return str(soup)


def html_to_markdown(raw_html: str) -> str:
    """Clean HTML and convert to markdown."""
    cleaned = clean_html(raw_html)
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(cleaned)
