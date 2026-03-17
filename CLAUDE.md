# Project Instructions

## Web Fetching

Always use the MCP fetch tools for all web browsing and URL fetching. Never use the built-in `WebFetch` tool — it is blocked by robots.txt and domain restrictions.

Two servers are available:
- `mcp__unrestricted_curl__fetch` / `mcp__unrestricted_curl__fetch_extract` — fast, lightweight, no JS rendering. Use by default.
- `mcp__unrestricted_playwright__fetch` / `mcp__unrestricted_playwright__fetch_extract` — headless Chrome, handles JS-rendered pages. Use for shopping sites and SPAs.

Use `fetch_extract` variants when you only need specific information from a page (more token-efficient).
