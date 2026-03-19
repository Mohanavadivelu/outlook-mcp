from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api, call_graph_api_paginated


def register(mcp):
    @mcp.tool()
    async def list_folders(
        include_item_counts: bool = True,
        include_children: bool = False,
    ) -> str:
        """List all mail folders in the mailbox.

        Args:
            include_item_counts: Include total and unread item counts. Default: True.
            include_children: Include child (sub) folders. Default: False.
        """
        access_token = await ensure_authenticated()

        response = await call_graph_api_paginated(
            access_token, "GET", "me/mailFolders", max_count=100
        )

        folders = response.get("value", [])
        if not folders:
            return "No mail folders found."

        lines = []
        for folder in folders:
            name = folder.get("displayName", "Unknown")
            folder_id = folder.get("id", "")

            line = f"- {name}"
            if include_item_counts:
                total = folder.get("totalItemCount", 0)
                unread = folder.get("unreadItemCount", 0)
                line += f" ({total} items, {unread} unread)"
            line += f"\n  ID: {folder_id}"

            lines.append(line)

            # Fetch child folders if requested
            if include_children and folder.get("childFolderCount", 0) > 0:
                try:
                    children = await call_graph_api(
                        access_token, "GET", f"me/mailFolders/{folder_id}/childFolders"
                    )
                    for child in children.get("value", []):
                        child_line = f"  └─ {child.get('displayName', 'Unknown')}"
                        if include_item_counts:
                            child_line += f" ({child.get('totalItemCount', 0)} items, {child.get('unreadItemCount', 0)} unread)"
                        child_line += f"\n     ID: {child.get('id', '')}"
                        lines.append(child_line)
                except Exception:
                    lines.append(f"  └─ (failed to load child folders)")

        return f"Mail folders ({len(folders)}):\n\n" + "\n\n".join(lines)
