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
    async def send_email(
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        is_html: bool = False,
        importance: str = "normal",
        save_to_sent: bool = True,
    ) -> str:
        """Compose and send an email.

        Args:
            to: Recipient email address(es), comma-separated for multiple.
            subject: Email subject line.
            body: Email body content.
            cc: CC recipient(s), comma-separated.
            bcc: BCC recipient(s), comma-separated.
            is_html: Whether the body is HTML (default: False, plain text).
            importance: Email importance: 'low', 'normal', or 'high'. Default: normal.
            save_to_sent: Save a copy to Sent Items folder. Default: True.
        """
        access_token = await ensure_authenticated()

        message = {
            "subject": subject,
            "body": {
                "contentType": "HTML" if is_html else "Text",
                "content": body,
            },
            "toRecipients": _parse_recipients(to),
            "importance": importance,
        }

        cc_recipients = _parse_recipients(cc)
        if cc_recipients:
            message["ccRecipients"] = cc_recipients

        bcc_recipients = _parse_recipients(bcc)
        if bcc_recipients:
            message["bccRecipients"] = bcc_recipients

        payload = {
            "message": message,
            "saveToSentItems": save_to_sent,
        }

        await call_graph_api(access_token, "POST", "me/sendMail", data=payload)

        recipients = to
        if cc:
            recipients += f" (CC: {cc})"
        if bcc:
            recipients += f" (BCC: {bcc})"

        return f"Email sent successfully.\nTo: {recipients}\nSubject: {subject}"
