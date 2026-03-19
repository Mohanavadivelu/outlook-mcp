"""Resolve mail folder names to Graph API endpoints."""

import urllib.parse
from utils.graph_api import call_graph_api

# Well-known folder name mappings
WELL_KNOWN_FOLDERS = {
    "inbox": "inbox",
    "drafts": "drafts",
    "sent": "sentItems",
    "sentitems": "sentItems",
    "deleted": "deletedItems",
    "deleteditems": "deletedItems",
    "junk": "junkemail",
    "junkemail": "junkemail",
    "spam": "junkemail",
    "archive": "archive",
}


async def resolve_folder_id(access_token: str, folder_name: str) -> str:
    """Resolve a folder name to its Graph API folder identifier.

    Args:
        access_token: Valid access token.
        folder_name: Display name or well-known name.

    Returns:
        The folder ID or well-known name for use in API paths.
    """
    normalized = folder_name.strip().lower()

    # Check well-known folders first
    if normalized in WELL_KNOWN_FOLDERS:
        return WELL_KNOWN_FOLDERS[normalized]

    # Look up custom folder by display name
    safe_name = folder_name.replace("'", "''")
    response = await call_graph_api(
        access_token,
        "GET",
        "me/mailFolders",
        query_params={"$filter": f"displayName eq '{safe_name}'"},
    )

    folders = response.get("value", [])
    if folders:
        return folders[0]["id"]

    # Fallback: return as-is (might be a folder ID already)
    return folder_name


async def resolve_folder_path(access_token: str, folder_name: str) -> str:
    """Resolve a folder name to its full Graph API messages endpoint.

    Args:
        access_token: Valid access token.
        folder_name: Display name or well-known name.

    Returns:
        Full API path like "me/mailFolders/inbox/messages".
    """
    folder_id = await resolve_folder_id(access_token, folder_name)
    encoded_id = urllib.parse.quote(folder_id, safe="")
    return f"me/mailFolders/{encoded_id}/messages"
