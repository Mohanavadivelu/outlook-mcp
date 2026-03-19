import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def register(mcp):
    @mcp.tool()
    async def mark_as_read(id: str, is_read: bool = True) -> str:
        """Mark an email as read or unread.

        Args:
            id: The email message ID.
            is_read: True to mark as read, False to mark as unread. Default: True.
        """
        access_token = await ensure_authenticated()

        encoded_id = urllib.parse.quote(id, safe="")
        await call_graph_api(
            access_token,
            "PATCH",
            f"me/messages/{encoded_id}",
            data={"isRead": is_read},
        )

        status = "read" if is_read else "unread"
        return f"Email marked as {status}."
