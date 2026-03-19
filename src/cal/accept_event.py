import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def register(mcp):
    @mcp.tool()
    async def accept_event(event_id: str, comment: str = "") -> str:
        """Accept a calendar event invitation.

        Args:
            event_id: The calendar event ID.
            comment: Optional comment to include with the acceptance.
        """
        access_token = await ensure_authenticated()

        encoded_id = urllib.parse.quote(event_id, safe="")
        data = {"sendResponse": True}
        if comment:
            data["comment"] = comment

        await call_graph_api(
            access_token, "POST", f"me/events/{encoded_id}/accept", data=data
        )

        return f"Event accepted.{f' Comment: {comment}' if comment else ''}"
