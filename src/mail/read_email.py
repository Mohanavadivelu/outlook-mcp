import urllib.parse
from config import EMAIL_DETAIL_FIELDS
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api
from utils.html_sanitizer import sanitize_html


def register(mcp):
    @mcp.tool()
    async def read_email(id: str, include_raw_html: bool = False) -> str:
        """Read the full content of a specific email by its ID.

        Args:
            id: The email message ID (obtained from list_emails or search_emails).
            include_raw_html: If True, include the raw HTML body alongside the sanitized text. Default: False.
        """
        access_token = await ensure_authenticated()

        encoded_id = urllib.parse.quote(id, safe="")
        email = await call_graph_api(
            access_token,
            "GET",
            f"me/messages/{encoded_id}",
            query_params={"$select": EMAIL_DETAIL_FIELDS},
        )

        # Build header info
        sender = email.get("from", {}).get("emailAddress", {})
        to_list = [
            f"{r['emailAddress'].get('name', '')} ({r['emailAddress'].get('address', '')})"
            for r in email.get("toRecipients", [])
        ]
        cc_list = [
            f"{r['emailAddress'].get('name', '')} ({r['emailAddress'].get('address', '')})"
            for r in email.get("ccRecipients", [])
        ]
        bcc_list = [
            f"{r['emailAddress'].get('name', '')} ({r['emailAddress'].get('address', '')})"
            for r in email.get("bccRecipients", [])
        ]

        parts = [
            f"Subject: {email.get('subject', '(no subject)')}",
            f"From: {sender.get('name', 'Unknown')} ({sender.get('address', '')})",
            f"To: {', '.join(to_list) if to_list else '(none)'}",
        ]
        if cc_list:
            parts.append(f"CC: {', '.join(cc_list)}")
        if bcc_list:
            parts.append(f"BCC: {', '.join(bcc_list)}")

        parts.append(f"Date: {email.get('receivedDateTime', '')}")
        parts.append(f"Importance: {email.get('importance', 'normal')}")
        parts.append(f"Read: {'Yes' if email.get('isRead') else 'No'}")
        parts.append(f"Attachments: {'Yes' if email.get('hasAttachments') else 'No'}")

        # Body
        body = email.get("body", {})
        body_content = body.get("content", "")
        content_type = body.get("contentType", "text")

        parts.append("")
        if content_type.lower() == "html":
            parts.append(sanitize_html(body_content))
            if include_raw_html:
                parts.append("")
                parts.append("--- RAW HTML ---")
                parts.append(body_content)
                parts.append("--- END RAW HTML ---")
        else:
            parts.append(f"--- BEGIN EMAIL BODY ---\n{body_content}\n--- END EMAIL BODY ---")

        parts.append("")
        parts.append(f"Message ID: {email.get('id', '')}")

        return "\n".join(parts)
