# Unrestricted Web Fetch for Claude Code

Claude Code's built-in `WebFetch` tool respects robots.txt and maintains a domain blocklist, which prevents it from fetching many websites. This project provides drop-in MCP servers that give Claude Code unrestricted web browsing — no robots.txt checks, no domain blocklist.

## Two servers

| Server | Script | Speed | JS support | Best for |
|--------|--------|-------|------------|----------|
| **unrestricted_curl** | `fetch_curl.py` | Fast (~instant) | No | Docs, wikis, news, APIs, most sites |
| **unrestricted_playwright** | `fetch_playwright.py` | Slower (~3-5s) | Yes | Shopping sites, SPAs, JS-rendered pages |

Each server exposes the same two tools:

| Tool | Description |
|------|-------------|
| `fetch` | Returns full page content as markdown (up to 200k chars) |
| `fetch_extract` | Fetches the page, then uses Claude Haiku to extract/summarize specific information (more token-efficient) |

**unrestricted_curl** uses `curl_cffi` with a Lynx (text browser) User-Agent, which avoids TLS fingerprint blocking and encourages servers to return server-rendered HTML.

**unrestricted_playwright** uses a persistent headless Chrome browser (via Playwright with stealth mode). The browser launches once per Claude Code session and is reused for all requests.

## Quick Start

### 1. Clone this repo

```bash
git clone https://github.com/aiba/claude-unrestricted-webfetch.git
```

### 2. Point Claude at it and go

Open Claude Code in any project and say:

> I cloned claude-unrestricted-webfetch to ~/git/claude-unrestricted-webfetch (or wherever you put it). Set it up so I have unrestricted web fetch. Install dependencies, configure the MCP servers, and update CLAUDE.md.

Claude will handle the rest — creating the venv, installing packages, configuring `.mcp.json`, permissions, and `CLAUDE.md`.

### Manual setup

If you prefer to set things up yourself:

<details>
<summary>Click to expand manual instructions</summary>

#### Install dependencies

```bash
cd claude-unrestricted-webfetch
python3 -m venv .venv
.venv/bin/pip install "mcp[cli]" curl_cffi playwright playwright-stealth html2text beautifulsoup4 lxml anthropic
.venv/bin/playwright install chromium
```

#### Configure Claude Code

Create `.mcp.json` in **your project** (the project where you want Claude to have unrestricted fetch). You can configure one or both servers:

```json
{
  "mcpServers": {
    "unrestricted_curl": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_curl.py"],
      "env": {
        "HTTPS_PROXY": "",
        "HTTP_PROXY": ""
      }
    },
    "unrestricted_playwright": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_playwright.py"],
      "env": {
        "HTTPS_PROXY": "",
        "HTTP_PROXY": ""
      }
    }
  }
}
```

Replace `/absolute/path/to/claude-unrestricted-webfetch` with the actual path where you cloned this repo.

Then create `.claude/settings.local.json` in your project to auto-approve the tools:

```json
{
  "permissions": {
    "allow": [
      "mcp__unrestricted_curl__fetch",
      "mcp__unrestricted_curl__fetch_extract",
      "mcp__unrestricted_playwright__fetch",
      "mcp__unrestricted_playwright__fetch_extract"
    ]
  },
  "enabledMcpjsonServers": [
    "unrestricted_curl",
    "unrestricted_playwright"
  ]
}
```

#### Tell Claude to use it

Add this to your project's `CLAUDE.md`:

```markdown
## Web Fetching

Always use the MCP fetch tools for all web browsing and URL fetching. Never use the built-in `WebFetch` tool — it is blocked by robots.txt and domain restrictions.

Two servers are available:
- `mcp__unrestricted_curl__fetch` / `mcp__unrestricted_curl__fetch_extract` — fast, lightweight, no JS rendering. Use by default.
- `mcp__unrestricted_playwright__fetch` / `mcp__unrestricted_playwright__fetch_extract` — headless Chrome, handles JS-rendered pages. Use for shopping sites and SPAs.

Use `fetch_extract` variants when you only need specific information from a page (more token-efficient).
```

</details>

### Restart Claude Code

```bash
claude
```

The MCP servers start automatically. You can verify they're working by asking Claude to fetch a normally-blocked site like reddit.com.

## Why not use a MITM proxy?

Our first approach was to route Claude Code's traffic through [mitmproxy](https://mitmproxy.org/) — intercepting requests to rewrite the User-Agent header and replace all `/robots.txt` responses with `Allow: /`. You can configure this via `HTTPS_PROXY` and `NODE_EXTRA_CA_CERTS` in `.claude/settings.local.json`.

The proxy itself works fine at the network level. However, Claude Code's built-in `WebFetch` tool enforces a **domain blocklist before the request is ever made**. For blocked domains (like reddit.com), the request never hits the network, so there's no traffic for the proxy to intercept. The rejection happens inside the tool itself.

An MCP server sidesteps this entirely — Claude calls our tool instead of `WebFetch`, and our tool makes its own HTTP requests with no restrictions.

## How it works

Both servers are lightweight Python [MCP](https://modelcontextprotocol.io/) servers that accept fetch requests from Claude Code over stdio and convert HTML to clean markdown via `html2text`.

**`fetch_curl.py`** makes direct HTTP requests using `curl_cffi` with a Lynx User-Agent. This avoids TLS fingerprint blocking that affects Python's `httpx`/`requests` and encourages servers to return server-rendered HTML instead of JS-dependent pages.

**`fetch_playwright.py`** launches a persistent headless Chromium browser with stealth mode. Each request opens a new tab, waits for the page to fully render (including JavaScript), extracts the HTML, and closes the tab. The browser stays running for the entire Claude Code session.

Both servers support `fetch_extract`, which sends the fetched markdown through Claude Haiku with your prompt to return only the relevant information.

## Requirements

- Python 3.10+
- Claude Code CLI
- `ANTHROPIC_API_KEY` environment variable set (used by `fetch_extract` for Haiku summarization; `fetch` works without one)

If you use Claude Code, you likely already have this set. If not:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Global Installation

To make the fetch tools available in **all** your Claude Code projects (not just one), add the MCP server config to your user-level settings instead:

**`~/.claude/.mcp.json`**:
```json
{
  "mcpServers": {
    "unrestricted_curl": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_curl.py"],
      "env": {
        "HTTPS_PROXY": "",
        "HTTP_PROXY": ""
      }
    },
    "unrestricted_playwright": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_playwright.py"],
      "env": {
        "HTTPS_PROXY": "",
        "HTTP_PROXY": ""
      }
    }
  }
}
```

**`~/.claude/settings.local.json`** (add to existing permissions):
```json
{
  "permissions": {
    "allow": [
      "mcp__unrestricted_curl__fetch",
      "mcp__unrestricted_curl__fetch_extract",
      "mcp__unrestricted_playwright__fetch",
      "mcp__unrestricted_playwright__fetch_extract"
    ]
  },
  "enabledMcpjsonServers": [
    "unrestricted_curl",
    "unrestricted_playwright"
  ]
}
```

## License

MIT
