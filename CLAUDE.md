# Project Instructions

## Web Fetching

Always use `mcp__fetch__fetch` or `mcp__fetch__fetch_extract` for all web browsing and URL fetching. Never use the built-in `WebFetch` tool — it is blocked by robots.txt and domain restrictions.

- Use `mcp__fetch__fetch_extract` when you only need specific information from a page (more token-efficient).
- Use `mcp__fetch__fetch` when you need the full page content.
