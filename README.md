# NotebookLM Consumer MCP Server

An MCP server for **Consumer NotebookLM** (notebooklm.google.com) - the free/personal tier.

> **Note:** This is NOT for NotebookLM Enterprise (Vertex AI). Those are completely separate systems.

## Features

| Tool | Description |
|------|-------------|
| `notebook_list` | List all notebooks |
| `notebook_create` | Create a new notebook |
| `notebook_get` | Get notebook details with sources |
| `notebook_add_url` | Add URL/YouTube as source |
| `notebook_add_text` | Add pasted text as source |
| `notebook_add_drive` | Add Google Drive document as source |
| `notebook_query` | Ask questions and get AI answers |

## Important Disclaimer

This MCP uses **reverse-engineered internal APIs** that:
- Are undocumented and may change without notice
- May violate Google's Terms of Service
- Require manual cookie extraction from your browser

Use at your own risk for personal/experimental purposes.

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/notebooklm-consumer-mcp.git
cd notebooklm-consumer-mcp

# Install with uv
uv tool install .
```

## Authentication Setup

### Option 1: Automated (Recommended)

Run the authentication CLI - it will launch Chrome and extract tokens automatically:

```bash
notebooklm-consumer-auth
```

This will:
1. Launch Chrome in headless mode to check if you're logged in
2. If not logged in, open a visible Chrome window for you to log in
3. Extract cookies and CSRF token automatically
4. Cache tokens to `~/.notebooklm-consumer/auth.json`

After authentication, just start the MCP server - it will use the cached tokens.

### Option 2: Manual (Environment Variables)

If you prefer manual extraction:

1. Go to `notebooklm.google.com` in Chrome and log in
2. Open DevTools (F12) > Network tab
3. Create a notebook or perform any action
4. Find a POST request to `/_/LabsTailwindUi/data/batchexecute`
5. Extract these values:

| Value | Where to Find |
|-------|---------------|
| Cookies | Request Headers > Cookie |
| CSRF Token | Request Body > `at=` parameter |
| Session ID | URL > `f.sid=` parameter |

6. Set environment variables:
```bash
export NOTEBOOKLM_COOKIES="SID=xxx; HSID=xxx; ..."
export NOTEBOOKLM_CSRF_TOKEN="ACi2F2Ox..."
export NOTEBOOKLM_SESSION_ID="1234567890"
```

## MCP Configuration

### Claude Code

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "notebooklm-consumer": {
      "command": "notebooklm-consumer-mcp"
    }
  }
}
```

If using the automated auth (Option 1), no environment variables are needed - the MCP server will use cached tokens from `~/.notebooklm-consumer/auth.json`.

For manual auth (Option 2), add environment variables:

```json
{
  "mcpServers": {
    "notebooklm-consumer": {
      "command": "notebooklm-consumer-mcp",
      "env": {
        "NOTEBOOKLM_COOKIES": "your-cookies-here",
        "NOTEBOOKLM_CSRF_TOKEN": "your-csrf-token",
        "NOTEBOOKLM_SESSION_ID": "your-session-id"
      }
    }
  }
}
```

## Usage Examples

### List Notebooks
```python
notebooks = notebook_list()
```

### Create and Query
```python
# Create a notebook
notebook = notebook_create(title="Research Project")

# Add sources
notebook_add_url(notebook_id, url="https://example.com/article")
notebook_add_text(notebook_id, text="My research notes...", title="Notes")

# Ask questions
result = notebook_query(notebook_id, query="What are the key points?")
print(result["answer"])
```

## Consumer vs Enterprise

| Feature | Consumer | Enterprise |
|---------|----------|------------|
| URL | notebooklm.google.com | vertexaisearch.cloud.google.com |
| Auth | Browser cookies | Google Cloud ADC |
| API | Internal RPCs | Discovery Engine API |
| Notebooks | Personal | Separate system |
| Audio Overviews | Yes | Yes |
| Video Overviews | Yes | No |
| Mind Maps | Yes | No |
| Flashcards/Quizzes | Yes | No |

## Limitations

- **Token expiration**: Cookies and CSRF tokens expire and need manual refresh
- **Rate limits**: Free tier has ~50 queries/day
- **No official support**: API may change without notice

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed API documentation and how to add new features.

## License

MIT License
