from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def _parse_recipients(addresses: str) -> list[dict]:
    """Parse comma-separated email addresses into Graph API recipient format."""
    if not addresses:
        return []
    return [
        {"emailAddress": {"address": addr.strip()}}
        for addr in addresses.split(",")
        if addr.strip()
    ]


def register(mcp):
    @mcp.tool()
    async def draft_email(
        to: str = "",
        subject: str = "",
        body: str = "",
        cc: str = "",
        bcc: str = "",
        importance: str = "normal",
    ) -> str:
        """Create and save an email draft without sending it.

        Args:
            to: Recipient email address(es), comma-separated.
            subject: Email subject line.
            body: Email body content (plain text).
            cc: CC recipient(s), comma-separated.
            bcc: BCC recipient(s), comma-separated.
            importance: Email importance: 'low', 'normal', or 'high'. Default: normal.
        """
        access_token = await ensure_authenticated()

        message = {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body,
            },
            "importance": importance,
        }

        to_recipients = _parse_recipients(to)
        if to_recipients:
            message["toRecipients"] = to_recipients

        cc_recipients = _parse_recipients(cc)
        if cc_recipients:
            message["ccRecipients"] = cc_recipients

        bcc_recipients = _parse_recipients(bcc)
        if bcc_recipients:
            message["bccRecipients"] = bcc_recipients

        result = await call_graph_api(access_token, "POST", "me/messages", data=message)

        draft_id = result.get("id", "unknown")
        return (
            f"Draft created successfully.\n"
            f"Subject: {subject}\n"
            f"Draft ID: {draft_id}\n"
            f"You can find it in your Drafts folder."
        )
