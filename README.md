# Unrestricted Web Fetch for Claude Code

Claude Code's built-in `WebFetch` tool respects robots.txt and maintains a domain blocklist, which prevents it from fetching many websites. This project provides a drop-in MCP server that gives Claude Code unrestricted web browsing — no robots.txt checks, no domain blocklist.

## What you get

Two tools available to Claude Code:

| Tool | Description | When to use |
|------|-------------|-------------|
| `fetch` | Returns full page content as markdown (up to 200k chars) | When Claude needs the complete page |
| `fetch_extract` | Fetches the page, then uses Claude Haiku to extract/summarize specific information | When you only need certain details (more token-efficient) |

Both tools use a Lynx (text browser) User-Agent, which encourages servers to return server-rendered HTML instead of JavaScript-dependent pages. Requests are made via `curl_cffi`, which avoids TLS fingerprint blocking that affects Python's `httpx`/`requests`.

## Quick Start

### 1. Clone this repo

```bash
git clone https://github.com/aiba/claude-unrestricted-webfetch.git
cd claude-unrestricted-webfetch
```

### 2. Install dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install "mcp[cli]" curl_cffi html2text anthropic
```

### 3. Configure Claude Code

Create `.mcp.json` in **your project** (the project where you want Claude to have unrestricted fetch):

```json
{
  "mcpServers": {
    "fetch": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_server.py"],
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
      "mcp__fetch__fetch",
      "mcp__fetch__fetch_extract"
    ]
  },
  "enabledMcpjsonServers": [
    "fetch"
  ]
}
```

### 4. Tell Claude to use it

Add this to your project's `CLAUDE.md`:

```markdown
## Web Fetching

Always use `mcp__fetch__fetch` or `mcp__fetch__fetch_extract` for all web browsing and URL fetching. Never use the built-in `WebFetch` tool.

- Use `mcp__fetch__fetch_extract` when you only need specific information from a page (more token-efficient).
- Use `mcp__fetch__fetch` when you need the full page content.
```

### 5. Restart Claude Code

```bash
claude
```

The fetch MCP server starts automatically. You can verify it's working by asking Claude to fetch a normally-blocked site like reddit.com.

## Why not use a MITM proxy?

Our first approach was to route Claude Code's traffic through [mitmproxy](https://mitmproxy.org/) — intercepting requests to rewrite the User-Agent header and replace all `/robots.txt` responses with `Allow: /`. You can configure this via `HTTPS_PROXY` and `NODE_EXTRA_CA_CERTS` in `.claude/settings.local.json`.

The proxy itself works fine at the network level. However, Claude Code's built-in `WebFetch` tool enforces a **domain blocklist before the request is ever made**. For blocked domains (like reddit.com), the request never hits the network, so there's no traffic for the proxy to intercept. The rejection happens inside the tool itself.

An MCP server sidesteps this entirely — Claude calls our tool instead of `WebFetch`, and our tool makes its own HTTP requests with no restrictions.

## How it works

`fetch_server.py` is a lightweight Python [MCP](https://modelcontextprotocol.io/) server that:

1. Accepts fetch requests from Claude Code over stdio
2. Fetches URLs directly with `curl_cffi` using a Lynx User-Agent (avoids TLS fingerprint blocking and encourages server-rendered HTML)
3. Converts HTML to clean markdown via `html2text`
4. For `fetch_extract`, sends the markdown through Claude Haiku with your prompt to return only the relevant information

No proxy, no middleware, no browser automation — just direct HTTP requests.

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
    "fetch": {
      "command": "/absolute/path/to/claude-unrestricted-webfetch/.venv/bin/python3",
      "args": ["/absolute/path/to/claude-unrestricted-webfetch/fetch_server.py"],
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
      "mcp__fetch__fetch",
      "mcp__fetch__fetch_extract"
    ]
  },
  "enabledMcpjsonServers": [
    "fetch"
  ]
}
```

## License

MIT
