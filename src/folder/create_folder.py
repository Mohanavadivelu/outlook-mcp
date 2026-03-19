import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api
from mail.folder_utils import resolve_folder_id


def register(mcp):
    @mcp.tool()
    async def create_folder(name: str, parent_folder: str = "") -> str:
        """Create a new mail folder.

        Args:
            name: Name for the new folder.
            parent_folder: Parent folder name or ID to create under. If empty, creates at top level.
        """
        access_token = await ensure_authenticated()

        data = {"displayName": name}

        if parent_folder:
            parent_id = await resolve_folder_id(access_token, parent_folder)
            encoded_parent = urllib.parse.quote(parent_id, safe="")
            endpoint = f"me/mailFolders/{encoded_parent}/childFolders"
        else:
            endpoint = "me/mailFolders"

        result = await call_graph_api(access_token, "POST", endpoint, data=data)

        folder_id = result.get("id", "unknown")
        parent_info = f" under '{parent_folder}'" if parent_folder else " at top level"
        return (
            f"Folder created successfully.\n"
            f"Name: {name}\n"
            f"Location: {parent_info}\n"
            f"Folder ID: {folder_id}"
        )
