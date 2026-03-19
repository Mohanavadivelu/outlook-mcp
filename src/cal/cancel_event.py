import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def register(mcp):
    @mcp.tool()
    async def cancel_event(event_id: str, comment: str = "") -> str:
        """Cancel a calendar event (organizer only).

        This sends cancellation notices to all attendees.

        Args:
            event_id: The calendar event ID.
            comment: Optional cancellation message for attendees.
        """
        access_token = await ensure_authenticated()

        encoded_id = urllib.parse.quote(event_id, safe="")
        data = {}
        if comment:
            data["comment"] = comment

        await call_graph_api(
            access_token, "POST", f"me/events/{encoded_id}/cancel", data=data
        )

        return f"Event cancelled. Cancellation notices sent to attendees.{f' Comment: {comment}' if comment else ''}"
