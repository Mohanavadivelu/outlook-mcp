from config import EMAIL_SELECT_FIELDS, MAX_RESULT_COUNT
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api_paginated
from mail.folder_utils import resolve_folder_path


def register(mcp):
    @mcp.tool()
    async def list_emails(folder: str = "inbox", count: int = 10) -> str:
        """Lists recent emails from a specified mail folder.

        Args:
            folder: Email folder to list (e.g., 'inbox', 'sent', 'drafts', 'deleted', 'junk', 'archive', or custom folder name). Default: inbox.
            count: Number of emails to retrieve (default: 10, max: 50).
        """
        access_token = await ensure_authenticated()
        count = min(count, MAX_RESULT_COUNT)
        endpoint = await resolve_folder_path(access_token, folder)

        query_params = {
            "$top": count,
            "$orderby": "receivedDateTime desc",
            "$select": EMAIL_SELECT_FIELDS,
        }

        response = await call_graph_api_paginated(
            access_token, "GET", endpoint, query_params, count
        )

        emails = response.get("value", [])
        if not emails:
            return f"No emails found in {folder}."

        lines = []
        for i, email in enumerate(emails, 1):
            sender = email.get("from", {}).get("emailAddress", {})
            date = email.get("receivedDateTime", "")
            read_status = "" if email.get("isRead") else "[UNREAD] "
            importance = ""
            if email.get("importance", "normal") == "high":
                importance = "[HIGH] "
            attachment = " [ATTACHMENT]" if email.get("hasAttachments") else ""

            lines.append(
                f"{i}. {read_status}{importance}{date}\n"
                f"   From: {sender.get('name', 'Unknown')} ({sender.get('address', '')})\n"
                f"   Subject: {email.get('subject', '(no subject)')}{attachment}\n"
                f"   Preview: {email.get('bodyPreview', '')[:100]}\n"
                f"   ID: {email['id']}"
            )

        return f"Found {len(emails)} emails in {folder}:\n\n" + "\n\n".join(lines)
