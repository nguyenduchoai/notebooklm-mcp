# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NotebookLM Consumer MCP Server** - Provides programmatic access to Consumer NotebookLM (notebooklm.google.com) using reverse-engineered internal APIs.

**IMPORTANT:** This is for the **Consumer/Free tier** of NotebookLM, NOT NotebookLM Enterprise (Vertex AI). These are completely separate systems with different notebooks, different APIs, and different authentication.

| Aspect | Consumer (this project) | Enterprise |
|--------|------------------------|------------|
| URL | notebooklm.google.com | vertexaisearch.cloud.google.com |
| Auth | Browser cookies + CSRF | Google Cloud ADC |
| API | Internal batchexecute RPC | Discovery Engine API |
| Stability | Undocumented, may break | Official, documented |

## Development Commands

```bash
# Install dependencies
uv tool install .

# Reinstall after code changes (ALWAYS clean cache first)
uv cache clean && uv tool install --force .

# Run the MCP server
notebooklm-consumer-mcp

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_function -v
```

**Python requirement:** >=3.11

## Authentication

### Method 1: Chrome DevTools MCP (Recommended)

If Chrome DevTools MCP is available, tokens can be extracted automatically:

```python
# 1. Find/navigate to NotebookLM page
# 2. Get cookies from a network request:
get_network_request(reqid=<batchexecute_request>)  # Cookie header

# 3. Extract CSRF token from page source:
evaluate_script(function="() => {
  const html = document.documentElement.outerHTML;
  const match = html.match(/\"SNlM0e\":\"([^\"]+)\"/);
  return match ? match[1] : null;
}")

# 4. Extract session ID from page source:
evaluate_script(function="() => {
  const html = document.documentElement.outerHTML;
  const match = html.match(/\"FdrFJe\":\"([^\"]+)\"/);
  return match ? match[1] : null;
}")

# 5. Save tokens via the MCP tool:
save_auth_tokens(cookies=<cookie_header>, csrf_token=<token>, session_id=<sid>)
```

### Method 2: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTEBOOKLM_COOKIES` | Yes | Full cookie header from Chrome DevTools |
| `NOTEBOOKLM_CSRF_TOKEN` | Yes | The `at=` value from request body |
| `NOTEBOOKLM_SESSION_ID` | No | The `f.sid=` value from URL |

### Essential Cookies

Only these cookies are required for authentication (the MCP automatically filters when saving):

| Cookie | Purpose |
|--------|---------|
| `SID`, `HSID`, `SSID`, `APISID`, `SAPISID` | Core auth (required) |
| `__Secure-1PSID`, `__Secure-3PSID` | Secure session variants |
| `__Secure-1PAPISID`, `__Secure-3PAPISID` | Secure API variants |
| `OSID`, `__Secure-OSID` | Origin-bound session |

Note: The full cookie header from network requests contains 20+ cookies, but `save_auth_tokens` automatically filters to only the 11 essential ones.

### Token Expiration

- **Cookies** (SID, HSID, SSID, APISID, SAPISID): Stable for weeks/months
- **CSRF token**: Changes on EVERY page reload
- **Session ID**: Changes on EVERY page reload

This means cached tokens may become stale. When API calls fail, refresh tokens via Chrome DevTools MCP.

## Architecture

```
src/notebooklm_consumer_mcp/
├── __init__.py      # Package version
├── server.py        # FastMCP server with tool definitions
├── api_client.py    # Internal API client (reverse-engineered)
├── auth.py          # Token caching and validation
└── auth_cli.py      # CLI for Chrome-based auth (notebooklm-consumer-auth)
```

**Executables:**
- `notebooklm-consumer-mcp` - The MCP server
- `notebooklm-consumer-auth` - CLI for extracting tokens (requires closing Chrome)

## API Discovery Documentation

This section documents everything discovered about the internal NotebookLM API through reverse engineering.

### Base Endpoint

```
POST https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute
```

### Request Format

```
Content-Type: application/x-www-form-urlencoded

f.req=<URL-encoded JSON>&at=<CSRF token>
```

The `f.req` structure:
```json
[[["<RPC_ID>", "<params_json>", null, "generic"]]]
```

### URL Query Parameters

| Param | Description |
|-------|-------------|
| `rpcids` | The RPC ID being called |
| `source-path` | Current page path (e.g., `/notebook/<id>`) |
| `bl` | Build/version string (e.g., `boq_labs-tailwind-frontend_20251217.10_p0`) |
| `f.sid` | Session ID |
| `hl` | Language code (e.g., `en`) |
| `_reqid` | Request counter |
| `rt` | Response type (`c`) |

### Response Format

```
)]}'
<byte_count>
<json_array>
```

- Starts with `)]}'` (anti-XSSI prefix) - MUST be stripped
- Followed by byte count, then JSON
- Multiple chunks may be present

### Known RPC IDs

| RPC ID | Purpose | Params Structure |
|--------|---------|------------------|
| `wXbhsf` | List notebooks | `[null, 1, null, [2]]` |
| `rLM1Ne` | Get notebook details | `[notebook_id, null, [2], null, 0]` |
| `CCqFvf` | Create notebook | `[title, null, null, [2], [1,null,null,null,null,null,null,null,null,null,[1]]]` |
| `s0tc2d` | Rename notebook | `[notebook_id, [[null, null, null, [null, "New Title"]]]]` |
| `WWINqb` | Delete notebook | `[[notebook_id], [2]]` |
| `izAoDd` | Add source (unified) | See source types below |
| `hizoJc` | Get source details | `[["source_id"], [2], [2]]` |
| `yR9Yof` | Check source freshness | `[null, ["source_id"], [2]]` → returns `false` if stale |
| `FLmJqe` | Sync Drive source | `[null, ["source_id"], [2]]` |
| `hPTbtc` | Get conversation IDs | `[notebook_id]` |
| `hT54vc` | User preferences | - |
| `ZwVcOc` | Settings | - |
| `ozz5Z` | Subscription info | - |

### Source Types (via `izAoDd` RPC)

All source types use the same RPC but with different param structures:

#### URL/YouTube Source
```python
source_data = [
    None,
    None,
    [url],  # URL at position 2
    None, None, None, None, None, None, None,
    1
]
params = [[[source_data]], notebook_id, [2], settings]
```

#### Pasted Text Source
```python
source_data = [
    None,
    [title, text_content],  # Title and content at position 1
    None,
    2,  # Type indicator at position 3
    None, None, None, None, None, None,
    1
]
params = [[[source_data]], notebook_id, [2], settings]
```

#### Google Drive Source
```python
source_data = [
    [document_id, mime_type, 1, title],  # Drive doc at position 0
    None, None, None, None, None, None, None, None, None,
    1
]
params = [[[source_data]], notebook_id, [2], settings]
```

**MIME Types:**
- `application/vnd.google-apps.document` - Google Docs
- `application/vnd.google-apps.presentation` - Google Slides
- `application/vnd.google-apps.spreadsheet` - Google Sheets
- `application/pdf` - PDF files

### Query Endpoint (Streaming)

Queries use a **different endpoint** - NOT batchexecute!

```
POST /_/LabsTailwindUi/data/google.internal.labs.tailwind.orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed
```

#### Query Request Structure
```python
params = [
    [  # Source IDs - each in nested array
        [[["source_id_1"]]],
        [[["source_id_2"]]],
    ],
    "Your question here",  # Query text
    None,
    [2, None, [1]],  # Config
    "conversation-uuid"  # For follow-up questions
]

f_req = [None, json.dumps(params)]
```

#### Query Response
Streaming JSON with multiple chunks:
1. **Thinking steps** - "Understanding...", "Exploring...", etc.
2. **Final answer** - Markdown formatted with citations
3. **Source references** - Links to specific passages in sources

### Key Findings

1. **Filtering is client-side**: The `wXbhsf` RPC returns ALL notebooks. "My notebooks" vs "Shared with me" filtering happens in the browser.

2. **Unified source RPC**: All source types (URL, text, Drive) use the same `izAoDd` RPC with different param structures.

3. **Query is streaming**: The query endpoint streams the AI's thinking process before the final answer.

4. **Conversation support**: Pass a `conversation_id` for multi-turn conversations (follow-up questions).

5. **Rate limits**: Free tier has ~50 queries/day limit.

## MCP Tools Provided

| Tool | Purpose |
|------|---------|
| `notebook_list` | List all notebooks |
| `notebook_create` | Create new notebook |
| `notebook_get` | Get notebook details |
| `notebook_rename` | Rename a notebook |
| `notebook_delete` | Delete a notebook (REQUIRES confirmation) |
| `notebook_add_url` | Add URL/YouTube source |
| `notebook_add_text` | Add pasted text source |
| `notebook_add_drive` | Add Google Drive source |
| `notebook_query` | Ask questions (AI answers!) |
| `source_list_drive` | List sources with types, check Drive freshness |
| `source_sync_drive` | Sync stale Drive sources (REQUIRES confirmation) |
| `save_auth_tokens` | Save tokens extracted via Chrome DevTools MCP |

**IMPORTANT - Operations Requiring Confirmation:**
- `notebook_delete` requires `confirm=True` - deletion is IRREVERSIBLE
- `source_sync_drive` requires `confirm=True` - always show stale sources first via `source_list_drive`

## Features NOT Yet Implemented

Consumer NotebookLM has many more features than Enterprise. To explore:

- [ ] **Audio Overviews** - Generate podcast-style discussions
- [ ] **Video Overviews** - Generate explainer videos
- [ ] **Mind Maps** - Visual knowledge maps
- [ ] **Flashcards** - Study cards from sources
- [ ] **Quizzes** - Interactive quizzes
- [ ] **Infographics** - Visual summaries
- [ ] **Slide Decks** - Presentation generation
- [ ] **Data Tables** - Structured data extraction
- [ ] **Reports** - Long-form reports
- [ ] **Notes** - Save chat responses as notes
- [ ] **Deep Research** - Extended web research
- [x] **Delete notebook** - Remove notebooks (RPC: `WWINqb`)
- [x] **Rename notebook** - Change notebook title (RPC: `s0tc2d`)
- [ ] **Delete source** - Remove sources
- [x] **Sync Drive sources** - Refresh Drive sources that changed (tools: `source_list_drive`, `source_sync_drive`)
- [ ] **Share notebook** - Collaboration features
- [ ] **Export** - Download content

## HIGH PRIORITY: Drive Source Sync Automation

**Problem:** NotebookLM doesn't auto-update Google Drive sources when the underlying document changes. Users must manually click each source → "Check freshness" → "Click to sync with Google Drive". For notebooks with many Drive sources, this is extremely tedious.

**Goal:** Automate syncing all Drive sources in a notebook with a single command.

### Discovery Checklist

- [x] **Identify Drive sources in get_notebook response** ✅
  - Source type is at **position 4** in the metadata array
  - See "Source Metadata Structure" below for complete documentation

- [x] **Capture "Check freshness" RPC** ✅
  - RPC ID: `yR9Yof`
  - Params: `[null, ["source_id"], [2]]`
  - Response: `[[null, false, ["source_id"]]]` where `false` = stale (needs sync), `true` = fresh

- [x] **Capture "Sync with Google Drive" RPC** ✅
  - RPC ID: `FLmJqe`
  - Params: `[null, ["source_id"], [2]]`
  - Response: Updated source info with new version hash and sync timestamp

- [x] **Capture "Get source details" RPC** ✅
  - RPC ID: `hizoJc`
  - Params: `[["source_id"], [2], [2]]`
  - Response: Full source details including Drive document ID, title, thumbnails

- [x] **Implement source type detection** ✅
  - Added `get_notebook_sources_with_types()` method in api_client.py
  - Returns source_type (1/2/4), source_type_name, and is_drive flag

- [x] **Implement sync_drive_sources tool** ✅
  - `source_list_drive`: Lists all sources, checks freshness for Drive sources
  - `source_sync_drive`: Syncs specified sources with confirmation

**Note:** MIME type (doc vs slides vs sheets) not available in notebook_get response.
Could be obtained via `hizoJc` RPC if needed in the future.

### Source Metadata Structure (from `rLM1Ne` response)

Each source in the notebook response has this structure:
```python
[
  [source_id],           # UUID for the source
  "Source Title",        # Display title
  [                      # Metadata array
    drive_doc_info,      # [0] null OR [doc_id, version_hash] for Drive/Gemini sources
    byte_count,          # [1] content size (0 for Drive, actual size for pasted text)
    [timestamp, nanos],  # [2] creation timestamp
    [version_uuid, [timestamp, nanos]],  # [3] last sync info
    source_type,         # [4] KEY FIELD: 1=Google Docs, 2=Slides/Sheets, 4=Pasted Text
    null,                # [5]
    null,                # [6]
    null,                # [7]
    content_bytes        # [8] actual byte count (for Drive sources after sync)
  ],
  [null, 2]              # Footer constant
]
```

**Source Types (metadata position 4):**
| Type | Meaning | Drive Doc Info | Can Sync |
|------|---------|----------------|----------|
| 1 | **Google Docs** (Documents, including Gemini Notes) | `[doc_id, version_hash]` | **Yes** |
| 2 | **Google Slides/Sheets** (Presentations & Spreadsheets) | `[doc_id, version_hash]` | **Yes** |
| 4 | Pasted text | `null` | No |

**Example - Type 2 (Slides/Sheets source that can be synced):**
```python
[
  ["627fceb0-b811-406d-a469-da584ea5a0dd"],
  "CY26 Commercial-Planning-Guide_Gold deck_WIP",
  [
    ["1uwEGv_nVyqf26K9MBnWAwztGL3q1ZsIk-CZItNkJQ7E", "QF3r1krI9fRXzA"],  # Drive doc ID + version
    0,
    [1766007264, 929458000],
    ["f78b157c-8732-41fc-a4d6-4db2353f7816", [1766377027, 620686000]],
    2,  # <-- SOURCE TYPE = Slides/Sheets
    ...
  ],
  [null, 2]
]
```

## How We Discovered This

### Method: Network Traffic Analysis

1. Used Chrome DevTools MCP to automate browser interactions
2. Captured network requests during each action
3. Decoded `f.req` body (URL-encoded JSON)
4. Analyzed response structures
5. Tested parameter variations

### Discovery Session Examples

**Creating a notebook:**
1. Clicked "Create notebook" button via Chrome DevTools
2. Captured POST to batchexecute with `rpcids=CCqFvf`
3. Decoded params: `["", null, null, [2], [1,null,...,[1]]]`
4. Response contained new notebook UUID at index 2

**Adding Drive source:**
1. Opened Add source > Drive picker
2. Double-clicked on a document
3. Captured POST with `rpcids=izAoDd`
4. Decoded: `[[[[doc_id, mime_type, 1, title], null,...,1]]]`
5. Different from URL/text which use different array positions

**Querying:**
1. Typed question in query box, clicked Submit
2. Found NEW endpoint: `GenerateFreeFormStreamed` (not batchexecute!)
3. Streaming response with thinking steps + final answer
4. Includes citations with source passage references

## Troubleshooting

### "401 Unauthorized" or "403 Forbidden"
- Cookies or CSRF token expired
- Re-extract from Chrome DevTools

### "Invalid CSRF token"
- The `at=` value expired
- Must match the current session

### Empty notebook list
- Session might be for a different Google account
- Verify you're logged into the correct account

### Rate limit errors
- Free tier: ~50 queries/day
- Wait until the next day or upgrade to Plus

## Contributing

When adding new features:

1. Use Chrome DevTools MCP to capture the network request
2. Document the RPC ID in this file
3. Add the param structure with comments
4. Update the api_client.py with the new method
5. Add corresponding tool in server.py
6. Update the "Features NOT Yet Implemented" checklist

## License

MIT License
