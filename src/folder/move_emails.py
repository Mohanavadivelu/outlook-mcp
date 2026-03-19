import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api
from mail.folder_utils import resolve_folder_id


def register(mcp):
    @mcp.tool()
    async def move_emails(email_ids: str, target_folder: str) -> str:
        """Move one or more emails to a different mail folder.

        Args:
            email_ids: Comma-separated email message IDs to move.
            target_folder: Target folder name (e.g., 'archive', 'deleted') or folder ID.
        """
        access_token = await ensure_authenticated()

        # Resolve target folder
        destination_id = await resolve_folder_id(access_token, target_folder)

        ids = [eid.strip() for eid in email_ids.split(",") if eid.strip()]
        if not ids:
            return "Error: No email IDs provided."

        success_count = 0
        errors = []

        for email_id in ids:
            try:
                encoded_id = urllib.parse.quote(email_id, safe="")
                await call_graph_api(
                    access_token,
                    "POST",
                    f"me/messages/{encoded_id}/move",
                    data={"destinationId": destination_id},
                )
                success_count += 1
            except Exception as e:
                errors.append(f"Failed to move {email_id[:20]}...: {e}")

        result = f"Moved {success_count}/{len(ids)} email(s) to '{target_folder}'."
        if errors:
            result += "\n\nErrors:\n" + "\n".join(errors)

        return result
