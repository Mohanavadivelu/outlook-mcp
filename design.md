# Outlook MCP Server — Python Rewrite Design Document

## 1. Overview

This document captures the design of an MCP (Model Context Protocol) server that provides AI assistants (Claude, ChatGPT, VS Code Copilot, etc.) with access to **Microsoft Outlook** services — Email, Calendar, Mail Folders, and Inbox Rules — via the **Microsoft Graph API**.

The server is to be rebuilt in **Python** using the official **MCP Python SDK** (`mcp[cli]` >= 1.2.0) and the `FastMCP` high-level API, as defined in the [MCP specification](https://modelcontextprotocol.io/docs/getting-started/intro) and [Build a Server quickstart](https://modelcontextprotocol.io/quickstart/server).

---

## 2. Architecture

### 2.1 MCP Concepts Used

| MCP Capability | Used? | Notes |
|----------------|-------|-------|
| **Tools** | Yes | Primary capability. All Outlook operations are exposed as tools. |
| Resources | No | Not needed — data is returned inline from tool calls. |
| Prompts | No | Not needed for this server. |

### 2.2 High-Level Architecture

```
┌─────────────────────────────────┐
│       MCP Host (Claude, etc.)   │
│         (MCP Client)            │
└──────────────┬──────────────────┘
               │  stdio (JSON-RPC)
               ▼
┌─────────────────────────────────┐
│     Outlook MCP Server (Python) │
│  ┌───────────────────────────┐  │
│  │       FastMCP Instance    │  │
│  │  (transport: stdio)       │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │      Tool Registry        │  │
│  │  @mcp.tool() decorators   │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │   Module Layer            │  │
│  │  ┌─────┐ ┌────────┐      │  │
│  │  │Auth │ │ Email   │      │  │
│  │  └─────┘ └────────┘      │  │
│  │  ┌─────────┐ ┌───────┐   │  │
│  │  │Calendar │ │Folder │   │  │
│  │  └─────────┘ └───────┘   │  │
│  │  ┌───────┐               │  │
│  │  │ Rules │               │  │
│  │  └───────┘               │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │   Graph API Client        │  │
│  │   (httpx async)           │  │
│  └────────────┬──────────────┘  │
│               │                 │
│  ┌────────────▼──────────────┐  │
│  │   Token Manager           │  │
│  │   (~/.outlook-mcp-tokens) │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
               │
               ▼ HTTPS
┌─────────────────────────────────┐
│  Microsoft Graph API            │
│  https://graph.microsoft.com/   │
│  v1.0/                          │
└─────────────────────────────────┘
```

### 2.3 Transport

- **Primary**: `stdio` — the server communicates over stdin/stdout using JSON-RPC, launched by the MCP host.
- **Important**: Never use `print()` to stdout. All debug/log output must go to `stderr` or use Python `logging` to stderr.

### 2.4 External Auth Server

A **separate** lightweight HTTP server (Flask/FastAPI) handles the OAuth browser redirect flow on `http://localhost:3333`. This is an independent process — it is NOT part of the MCP stdio server.

---

## 3. Configuration

### 3.1 Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `MS_CLIENT_ID` | `.env` file | Azure App Registration Client ID |
| `MS_CLIENT_SECRET` | `.env` file | Azure App Registration Client Secret **VALUE** (not Secret ID) |
| `MS_TENANT_ID` | `.env` file | Azure Tenant ID (default: `common`) |
| `MS_REDIRECT_URI` | `.env` file | OAuth redirect URI (default: `http://localhost:3333/auth/callback`) |
| `MS_SCOPES` | `.env` file | Space-separated OAuth scopes |
| `OUTLOOK_CLIENT_ID` | Claude Desktop config | Alternative var name for Claude Desktop JSON config |
| `OUTLOOK_CLIENT_SECRET` | Claude Desktop config | Alternative var name for Claude Desktop JSON config |
| `USE_TEST_MODE` | `.env` / env | Set to `true` to use mock data |

### 3.2 Constants

```python
SERVER_NAME = "outlook-mcp"
SERVER_VERSION = "1.0.0"

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/"

OAUTH_SCOPES = [
    "offline_access",
    "User.Read",
    "Mail.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.Read",
    "Calendars.ReadWrite",
]

TOKEN_STORE_PATH = "~/.outlook-mcp-tokens.json"
AUTH_SERVER_URL = "http://localhost:3333"

DEFAULT_PAGE_SIZE = 25
MAX_RESULT_COUNT = 50
DEFAULT_TIMEZONE = "Central European Standard Time"

# Graph API field selections (OData $select)
EMAIL_SELECT_FIELDS = "id,subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,hasAttachments,importance,isRead"
EMAIL_DETAIL_FIELDS = "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,bodyPreview,body,hasAttachments,importance,isRead,internetMessageHeaders"
CALENDAR_SELECT_FIELDS = "id,subject,bodyPreview,start,end,location,organizer,attendees,isAllDay,isCancelled"
```

### 3.3 Claude Desktop Integration

```json
{
  "mcpServers": {
    "outlook": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/outlook-mcp-python",
        "run",
        "server.py"
      ],
      "env": {
        "OUTLOOK_CLIENT_ID": "<your-client-id>",
        "OUTLOOK_CLIENT_SECRET": "<your-client-secret>"
      }
    }
  }
}
```

---

## 4. Authentication Design

### 4.1 OAuth 2.0 Authorization Code Flow

```
User ──► authenticate tool ──► returns auth URL
User ──► opens URL in browser ──► Microsoft login
Microsoft ──► redirects to localhost:3333/auth/callback with code
Auth Server ──► exchanges code for tokens via POST to token endpoint
Auth Server ──► saves tokens to ~/.outlook-mcp-tokens.json
```

### 4.2 Token Storage

Tokens are persisted in a JSON file at `~/.outlook-mcp-tokens.json`:

```json
{
  "access_token": "eyJ0eX...",
  "refresh_token": "0.AXEA...",
  "expires_at": 1710000000000,
  "expires_in": 3600
}
```

### 4.3 Token Manager Module (`auth/token_manager.py`)

| Function | Description |
|----------|-------------|
| `load_tokens()` | Read and parse tokens from JSON file. Return `None` if missing/expired. |
| `save_tokens(tokens)` | Write tokens dict to JSON file. |
| `get_access_token()` | Return cached token or load from file. Return `None` if expired. |
| `refresh_access_token()` | Use refresh_token to get new access_token via Microsoft token endpoint. Save updated tokens. |
| `get_valid_access_token()` | Load tokens → check expiry → refresh if needed → return valid access_token or `None`. |

### 4.4 OAuth Auth Server (`auth_server.py`) — Separate Process

A minimal HTTP server (Flask or built-in `http.server`) running on port 3333 with these routes:

| Route | Method | Description |
|-------|--------|-------------|
| `/auth` | GET | Builds Microsoft OAuth authorize URL with PKCE/state, redirects browser |
| `/auth/callback` | GET | Receives auth code, exchanges for tokens, saves to file |
| `/token-status` | GET | Returns current token validity status |

**Security**: Generate a random `state` parameter for CSRF protection. Validate it in the callback.

### 4.5 `ensure_authenticated()` Helper

Every tool handler calls this before making Graph API requests:

```python
async def ensure_authenticated() -> str:
    """Returns a valid access token or raises an error."""
    token = get_valid_access_token()
    if not token:
        raise AuthenticationRequiredError("Authentication required. Use the 'authenticate' tool first.")
    return token
```

---

## 5. Graph API Client (`utils/graph_api.py`)

### 5.1 Core HTTP Client

Uses `httpx.AsyncClient` for all Microsoft Graph API calls.

```python
async def call_graph_api(
    access_token: str,
    method: str,         # GET, POST, PATCH, DELETE
    path: str,           # e.g. "me/messages" or full URL for pagination
    data: dict = None,   # Request body for POST/PATCH
    query_params: dict = None  # OData query parameters
) -> dict:
```

**Behavior**:
- Prepends `https://graph.microsoft.com/v1.0/` unless path is already a full URL (pagination `@odata.nextLink`).
- Sets `Authorization: Bearer {token}` and `Content-Type: application/json`.
- Returns parsed JSON response.
- Raises specific errors: `UnauthorizedError` for 401, `GraphAPIError` for other failures.
- In test mode (`USE_TEST_MODE=true`), returns mock data instead of making real HTTP calls.

### 5.2 Paginated Client

```python
async def call_graph_api_paginated(
    access_token: str,
    method: str,
    path: str,
    query_params: dict = None,
    max_count: int = 0
) -> dict:
```

**Behavior**:
- Follows `@odata.nextLink` URLs to fetch subsequent pages.
- Accumulates results until `max_count` is reached or no more pages.
- Returns `{"value": [...all_items...]}`.

### 5.3 HTML Sanitizer (`utils/html_sanitizer.py`)

Security-focused function that extracts **only visible text** from HTML email bodies:

- Removes `<script>`, `<style>`, `<head>`, `<iframe>`, etc.
- Removes HTML comments (prevent prompt injection).
- Strips elements with hiding CSS: `display:none`, `visibility:hidden`, `opacity:0`, `font-size:0`, etc.
- Strips elements with `hidden` attribute or `aria-hidden="true"`.
- Removes invisible Unicode characters (zero-width spaces, etc.).
- Converts block elements to newlines for readability.
- Wraps output in boundary markers for LLM safety.

---

## 6. Tool Definitions

All tools are registered using the `@mcp.tool()` decorator from `FastMCP`. The Python SDK auto-generates `inputSchema` from type hints and docstrings.

### 6.1 Auth Tools (3 tools)

| Tool Name | Description | Parameters | Graph API Endpoint |
|-----------|-------------|------------|--------------------|
| `about` | Returns server info and capabilities | *(none)* | *(none)* |
| `authenticate` | Initiates OAuth flow, returns auth URL | `force: bool = False` | *(none — returns URL)* |
| `check_auth_status` | Checks if currently authenticated | *(none)* | *(none)* |

### 6.2 Email Tools (6 tools)

| Tool Name | Description | Parameters | Graph API |
|-----------|-------------|------------|-----------|
| `list_emails` | List recent emails from a folder | `folder: str = "inbox"`, `count: int = 10` | `GET me/mailFolders/{id}/messages` |
| `search_emails` | Search emails with various criteria | `query: str`, `folder: str`, `from_addr: str`, `to: str`, `subject: str`, `has_attachments: bool`, `unread_only: bool`, `count: int` | `GET me/mailFolders/{id}/messages` with `$search` (KQL) or `$filter` |
| `read_email` | Read full content of a specific email | `id: str` *(required)*, `include_raw_html: bool = False` | `GET me/messages/{id}` |
| `send_email` | Compose and send an email | `to: str` *(required)*, `subject: str` *(required)*, `body: str` *(required)*, `cc: str`, `bcc: str`, `is_html: bool`, `importance: str`, `save_to_sent: bool` | `POST me/sendMail` |
| `draft_email` | Create and save an email draft | `to: str`, `cc: str`, `bcc: str`, `subject: str`, `body: str`, `importance: str` | `POST me/messages` |
| `mark_as_read` | Mark email as read/unread | `id: str` *(required)*, `is_read: bool = True` | `PATCH me/messages/{id}` |

#### Email Search Strategy (Progressive Fallback)

The search implementation uses a progressive fallback strategy:

1. **Combined search** — Use `$search` with all KQL terms (from, to, subject, query) + boolean filters
2. **Single-term search** — Try each term individually (subject → from → to → query)
3. **Boolean filters only** — Use `$filter` with `hasAttachments`, `isRead`
4. **Fallback** — Return recent emails sorted by date

This is necessary because Microsoft Graph's `$search` does not support `$orderby` or `$filter` simultaneously, and KQL support varies.

#### Folder Resolution

Emails can be listed/searched in any mail folder. Folder name → endpoint resolution:

| Input | Resolved Endpoint |
|-------|-------------------|
| `inbox` | `me/mailFolders/inbox/messages` |
| `drafts` | `me/mailFolders/drafts/messages` |
| `sent` | `me/mailFolders/sentItems/messages` |
| `deleted` | `me/mailFolders/deletedItems/messages` |
| `junk` | `me/mailFolders/junkemail/messages` |
| `archive` | `me/mailFolders/archive/messages` |
| *(custom name)* | Look up via `GET me/mailFolders?$filter=displayName eq '{name}'` → use folder ID |

### 6.3 Calendar Tools (5 tools)

| Tool Name | Description | Parameters | Graph API |
|-----------|-------------|------------|-----------|
| `list_events` | List upcoming calendar events | `count: int = 10` | `GET me/events` with `$filter=start/dateTime ge '{now}'` and `$orderby=start/dateTime` |
| `create_event` | Create a new calendar event | `subject: str` *(req)*, `start: str` *(req, ISO 8601)*, `end: str` *(req, ISO 8601)*, `attendees: list[str]`, `body: str` | `POST me/events` |
| `accept_event` | Accept a calendar invitation | `event_id: str` *(req)*, `comment: str` | `POST me/events/{id}/accept` |
| `decline_event` | Decline a calendar invitation | `event_id: str` *(req)*, `comment: str` | `POST me/events/{id}/decline` |
| `cancel_event` | Cancel a calendar event (organizer) | `event_id: str` *(req)*, `comment: str` | `POST me/events/{id}/cancel` |
| `delete_event` | Delete a calendar event | `event_id: str` *(req)* | `DELETE me/events/{id}` |

**Note on Time Zones**: Event start/end are sent as `{ dateTime, timeZone }` objects. Default timezone is configurable (`DEFAULT_TIMEZONE`).

### 6.4 Folder Tools (3 tools)

| Tool Name | Description | Parameters | Graph API |
|-----------|-------------|------------|-----------|
| `list_folders` | List all mail folders | `include_item_counts: bool`, `include_children: bool` | `GET me/mailFolders` + `GET me/mailFolders/{id}/childFolders` |
| `create_folder` | Create a new mail folder | `name: str` *(req)*, `parent_folder: str` | `POST me/mailFolders` or `POST me/mailFolders/{parentId}/childFolders` |
| `move_emails` | Move emails between folders | `email_ids: str` *(req, comma-separated)*, `target_folder: str` *(req)*, `source_folder: str` | `POST me/messages/{id}/move` with `{ destinationId }` |

### 6.5 Rules Tools (3 tools)

| Tool Name | Description | Parameters | Graph API |
|-----------|-------------|------------|-----------|
| `list_rules` | List inbox message rules | `include_details: bool` | `GET me/mailFolders/inbox/messageRules` |
| `create_rule` | Create a new inbox rule | `name: str` *(req)*, `from_addresses: str`, `contains_subject: str`, `has_attachments: bool`, `move_to_folder: str`, `mark_as_read: bool`, `is_enabled: bool`, `sequence: int` | `POST me/mailFolders/inbox/messageRules` |
| `edit_rule_sequence` | Change rule execution order | `rule_name: str` *(req)*, `sequence: int` *(req)* | `PATCH me/mailFolders/inbox/messageRules/{id}` |

**Rule Structure** sent to Graph API:
```json
{
  "displayName": "Move GitHub Emails",
  "isEnabled": true,
  "sequence": 1,
  "conditions": {
    "fromAddresses": [{ "emailAddress": { "address": "notifications@github.com" } }],
    "subjectContains": ["[repo-name]"],
    "hasAttachment": false
  },
  "actions": {
    "moveToFolder": "<folder-id>",
    "markAsRead": true
  }
}
```

---

## 7. Python Project Structure

```
outlook-mcp-python/
├── pyproject.toml              # Project metadata, dependencies (uv/pip)
├── server.py                   # Entry point — FastMCP instance, tool registration
├── config.py                   # Constants, env var loading
├── auth_server.py              # Standalone OAuth HTTP server (port 3333)
│
├── auth/
│   ├── __init__.py
│   ├── token_manager.py        # Token load/save/refresh/validate
│   └── tools.py                # about, authenticate, check_auth_status tools
│
├── email/
│   ├── __init__.py
│   ├── list_emails.py          # list_emails tool
│   ├── search_emails.py        # search_emails tool (progressive fallback)
│   ├── read_email.py           # read_email tool (with HTML sanitization)
│   ├── send_email.py           # send_email tool
│   ├── draft_email.py          # draft_email tool
│   ├── mark_as_read.py         # mark_as_read tool
│   └── folder_utils.py         # Folder name → endpoint resolution, well-known folders
│
├── calendar/
│   ├── __init__.py
│   ├── list_events.py          # list_events tool
│   ├── create_event.py         # create_event tool
│   ├── accept_event.py         # accept_event tool
│   ├── decline_event.py        # decline_event tool
│   ├── cancel_event.py         # cancel_event tool
│   └── delete_event.py         # delete_event tool
│
├── folder/
│   ├── __init__.py
│   ├── list_folders.py         # list_folders tool
│   ├── create_folder.py        # create_folder tool
│   └── move_emails.py          # move_emails tool
│
├── rules/
│   ├── __init__.py
│   ├── list_rules.py           # list_rules tool
│   ├── create_rule.py          # create_rule tool
│   └── edit_rule_sequence.py   # edit_rule_sequence tool
│
├── utils/
│   ├── __init__.py
│   ├── graph_api.py            # call_graph_api, call_graph_api_paginated
│   ├── html_sanitizer.py       # HTML → safe text extraction
│   └── mock_data.py            # Test mode mock responses
│
└── tests/
    ├── test_html_sanitizer.py
    ├── test_token_storage.py
    ├── test_email_list.py
    └── ...
```

---

## 8. Python Implementation Pattern

### 8.1 Entry Point (`server.py`)

```python
import logging
import sys
from mcp.server.fastmcp import FastMCP
from config import SERVER_NAME

# Configure logging to stderr (CRITICAL for stdio transport)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(SERVER_NAME)

# Initialize FastMCP server
mcp = FastMCP(SERVER_NAME)

# Import and register all tool modules
# Each module uses @mcp.tool() to register its tools
from auth.tools import register_tools as register_auth_tools
from email import register_tools as register_email_tools
from calendar import register_tools as register_calendar_tools
from folder import register_tools as register_folder_tools
from rules import register_tools as register_rules_tools

register_auth_tools(mcp)
register_email_tools(mcp)
register_calendar_tools(mcp)
register_folder_tools(mcp)
register_rules_tools(mcp)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### 8.2 Tool Implementation Pattern (Example: `list_emails`)

```python
# email/list_emails.py
from config import EMAIL_SELECT_FIELDS, MAX_RESULT_COUNT
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api_paginated
from email.folder_utils import resolve_folder_path


def register(mcp):
    @mcp.tool()
    async def list_emails(folder: str = "inbox", count: int = 10) -> str:
        """Lists recent emails from a specified folder.

        Args:
            folder: Email folder to list (e.g., 'inbox', 'sent', 'drafts'). Default: inbox.
            count: Number of emails to retrieve (default: 10, max: 50).
        """
        access_token = await ensure_authenticated()
        endpoint = await resolve_folder_path(access_token, folder)

        query_params = {
            "$top": min(50, count),
            "$orderby": "receivedDateTime desc",
            "$select": EMAIL_SELECT_FIELDS,
        }

        response = await call_graph_api_paginated(
            access_token, "GET", endpoint, query_params, count
        )

        if not response.get("value"):
            return f"No emails found in {folder}."

        lines = []
        for i, email in enumerate(response["value"], 1):
            sender = email.get("from", {}).get("emailAddress", {})
            date = email.get("receivedDateTime", "")
            read_status = "" if email.get("isRead") else "[UNREAD] "
            lines.append(
                f"{i}. {read_status}{date} - From: {sender.get('name', 'Unknown')} ({sender.get('address', '')})\n"
                f"   Subject: {email.get('subject', '(no subject)')}\n"
                f"   ID: {email['id']}"
            )

        return f"Found {len(response['value'])} emails in {folder}:\n\n" + "\n\n".join(lines)
```

### 8.3 Error Handling Pattern

Every tool handler follows this pattern:
1. Call `ensure_authenticated()` — raises `AuthenticationRequiredError` if not authenticated.
2. Make Graph API call(s).
3. Return a formatted text string on success.
4. Catch expected errors and return user-friendly messages.

```python
class AuthenticationRequiredError(Exception):
    pass

class GraphAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Graph API error ({status_code}): {message}")
```

Tool functions return `str` — the MCP SDK wraps this into the standard `{ content: [{ type: "text", text: "..." }] }` response format automatically.

---

## 9. Dependencies

```toml
# pyproject.toml
[project]
name = "outlook-mcp"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.2.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
auth-server = [
    "flask>=3.0.0",       # For the standalone OAuth server
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

---

## 10. Microsoft Graph API Reference

### 10.1 Endpoints Used

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List emails | GET | `me/mailFolders/{folder}/messages` |
| Search emails | GET | `me/mailFolders/{folder}/messages?$search="..."` |
| Read email | GET | `me/messages/{id}` |
| Send email | POST | `me/sendMail` |
| Create draft | POST | `me/messages` |
| Mark as read | PATCH | `me/messages/{id}` |
| List events | GET | `me/events` |
| Create event | POST | `me/events` |
| Accept event | POST | `me/events/{id}/accept` |
| Decline event | POST | `me/events/{id}/decline` |
| Cancel event | POST | `me/events/{id}/cancel` |
| Delete event | DELETE | `me/events/{id}` |
| List folders | GET | `me/mailFolders` |
| List child folders | GET | `me/mailFolders/{id}/childFolders` |
| Create folder | POST | `me/mailFolders` or `me/mailFolders/{parentId}/childFolders` |
| Move email | POST | `me/messages/{id}/move` |
| List rules | GET | `me/mailFolders/inbox/messageRules` |
| Create rule | POST | `me/mailFolders/inbox/messageRules` |
| Update rule | PATCH | `me/mailFolders/inbox/messageRules/{id}` |

### 10.2 Azure App Registration Required Permissions

| Permission | Type | Description |
|------------|------|-------------|
| `Mail.Read` | Delegated | Read user mail |
| `Mail.ReadWrite` | Delegated | Read/write user mail (drafts, mark as read, move) |
| `Mail.Send` | Delegated | Send mail as user |
| `Calendars.Read` | Delegated | Read user calendars |
| `Calendars.ReadWrite` | Delegated | Create/modify/delete events |
| `User.Read` | Delegated | Read user profile |
| `offline_access` | Delegated | Maintain refresh tokens |

### 10.3 Pagination

Microsoft Graph uses `@odata.nextLink` for pagination. The paginated client follows these links automatically up to `max_count`.

---

## 11. Test Mode

When `USE_TEST_MODE=true`, the Graph API client returns mock data instead of making real HTTP calls. Mock data is defined in `utils/mock_data.py` and covers:
- Email listings
- Email detail reads
- Calendar events
- Folder listings
- Send/create operations (return success responses)

---

## 12. Security Considerations

1. **HTML Sanitization**: Email bodies in HTML are sanitized to prevent prompt injection via hidden content (hidden CSS, invisible Unicode, HTML comments, etc.).
2. **OAuth State Parameter**: CSRF protection via random state parameter in OAuth flow.
3. **Token Storage**: Tokens stored in user home directory with restrictive permissions.
4. **No stdout in stdio mode**: All logging goes to stderr to avoid corrupting JSON-RPC.
5. **Input Validation**: All required parameters validated before making API calls.
6. **URL Encoding**: Email IDs and folder IDs are `encodeURIComponent`-encoded in API paths.

---

## 13. Summary of All 20 Tools

| # | Tool | Module | Description |
|---|------|--------|-------------|
| 1 | `about` | auth | Server info |
| 2 | `authenticate` | auth | Start OAuth flow |
| 3 | `check_auth_status` | auth | Check token status |
| 4 | `list_emails` | email | List emails from folder |
| 5 | `search_emails` | email | Search with criteria |
| 6 | `read_email` | email | Read full email content |
| 7 | `send_email` | email | Send a new email |
| 8 | `draft_email` | email | Create email draft |
| 9 | `mark_as_read` | email | Mark email read/unread |
| 10 | `list_events` | calendar | List upcoming events |
| 11 | `create_event` | calendar | Create calendar event |
| 12 | `accept_event` | calendar | Accept invitation |
| 13 | `decline_event` | calendar | Decline invitation |
| 14 | `cancel_event` | calendar | Cancel event (organizer) |
| 15 | `delete_event` | calendar | Delete event |
| 16 | `list_folders` | folder | List mail folders |
| 17 | `create_folder` | folder | Create mail folder |
| 18 | `move_emails` | folder | Move emails to folder |
| 19 | `list_rules` | rules | List inbox rules |
| 20 | `create_rule` | rules | Create inbox rule |
| 21 | `edit_rule_sequence` | rules | Change rule priority |
