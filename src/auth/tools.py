import secrets
import urllib.parse
from config import (
    SERVER_NAME,
    SERVER_VERSION,
    MS_CLIENT_ID,
    MS_TENANT_ID,
    MS_REDIRECT_URI,
    OAUTH_SCOPES,
    AUTH_SERVER_URL,
)
from auth.token_manager import get_valid_access_token


def register_tools(mcp):

    @mcp.tool()
    async def about() -> str:
        """Returns information about the Outlook MCP server and its capabilities."""
        tools = [
            "about", "authenticate", "check_auth_status",
            "list_emails", "search_emails", "read_email", "send_email", "draft_email", "mark_as_read",
            "list_events", "create_event", "accept_event", "decline_event", "cancel_event", "delete_event",
            "list_folders", "create_folder", "move_emails",
            "list_rules", "create_rule", "edit_rule_sequence",
        ]
        return (
            f"Server: {SERVER_NAME} v{SERVER_VERSION}\n"
            f"Description: MCP server for Microsoft Outlook via Graph API\n"
            f"Transport: stdio\n"
            f"Tools ({len(tools)}): {', '.join(tools)}\n\n"
            f"Capabilities:\n"
            f"  - Email: List, search, read, send, draft, mark as read\n"
            f"  - Calendar: List, create, accept, decline, cancel, delete events\n"
            f"  - Folders: List, create, move emails between folders\n"
            f"  - Rules: List, create, edit inbox rules\n\n"
            f"Use 'authenticate' to connect your Microsoft account."
        )

    @mcp.tool()
    async def authenticate(force: bool = False) -> str:
        """Initiates the Microsoft OAuth authentication flow.

        Returns a URL that the user must open in their browser to sign in.

        Args:
            force: Force re-authentication even if already authenticated.
        """
        if not force:
            token = await get_valid_access_token()
            if token:
                return (
                    "Already authenticated with Microsoft.\n"
                    "Use force=True to re-authenticate."
                )

        if not MS_CLIENT_ID:
            return (
                "Error: MS_CLIENT_ID (or OUTLOOK_CLIENT_ID) environment variable is not set.\n"
                "Please configure your Azure App Registration credentials."
            )

        state = secrets.token_urlsafe(32)

        params = {
            "client_id": MS_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": MS_REDIRECT_URI,
            "scope": " ".join(OAUTH_SCOPES),
            "response_mode": "query",
            "state": state,
        }

        auth_url = (
            f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/authorize?"
            + urllib.parse.urlencode(params)
        )

        return (
            "To authenticate with Microsoft Outlook:\n\n"
            f"1. Make sure the auth server is running:\n"
            f"   python auth_server.py\n\n"
            f"2. Open this URL in your browser:\n"
            f"   {auth_url}\n\n"
            f"3. Sign in with your Microsoft account and grant permissions.\n\n"
            f"4. After signing in, use 'check_auth_status' to verify."
        )

    @mcp.tool()
    async def check_auth_status() -> str:
        """Checks whether the server is currently authenticated with Microsoft."""
        token = await get_valid_access_token()
        if token:
            return "Authenticated: Yes\nStatus: Valid access token available."
        else:
            return (
                "Authenticated: No\n"
                "Status: No valid access token. Use the 'authenticate' tool to sign in."
            )
