import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def register(mcp):
    @mcp.tool()
    async def delete_event(event_id: str) -> str:
        """Delete a calendar event permanently.

        Args:
            event_id: The calendar event ID.
        """
        access_token = await ensure_authenticated()

        encoded_id = urllib.parse.quote(event_id, safe="")
        await call_graph_api(
            access_token, "DELETE", f"me/events/{encoded_id}"
        )

        return "Event deleted successfully."
