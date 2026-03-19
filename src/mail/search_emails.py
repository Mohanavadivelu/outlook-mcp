import logging
from config import EMAIL_SELECT_FIELDS, MAX_RESULT_COUNT
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api_paginated, GraphAPIError
from mail.folder_utils import resolve_folder_path

logger = logging.getLogger("outlook-mcp")


def _build_kql_search(query: str = "", from_addr: str = "", to: str = "", subject: str = "") -> str:
    """Build a KQL search string for Graph API $search parameter."""
    parts = []
    if from_addr:
        parts.append(f"from:{from_addr}")
    if to:
        parts.append(f"to:{to}")
    if subject:
        parts.append(f"subject:{subject}")
    if query:
        parts.append(query)
    return " ".join(parts)


def _build_filter(has_attachments: bool | None = None, unread_only: bool = False) -> str:
    """Build an OData $filter string."""
    filters = []
    if has_attachments is not None:
        filters.append(f"hasAttachments eq {str(has_attachments).lower()}")
    if unread_only:
        filters.append("isRead eq false")
    return " and ".join(filters)


def register(mcp):
    @mcp.tool()
    async def search_emails(
        query: str = "",
        folder: str = "inbox",
        from_addr: str = "",
        to: str = "",
        subject: str = "",
        has_attachments: bool | None = None,
        unread_only: bool = False,
        count: int = 10,
    ) -> str:
        """Search emails with various criteria using progressive fallback strategy.

        Args:
            query: Free-text search query.
            folder: Folder to search in (default: inbox).
            from_addr: Filter by sender email address.
            to: Filter by recipient email address.
            subject: Filter by subject text.
            has_attachments: Filter by attachment presence (True/False/None).
            unread_only: Only return unread emails.
            count: Maximum results (default: 10, max: 50).
        """
        access_token = await ensure_authenticated()
        count = min(count, MAX_RESULT_COUNT)
        endpoint = await resolve_folder_path(access_token, folder)

        kql = _build_kql_search(query, from_addr, to, subject)
        boolean_filter = _build_filter(has_attachments, unread_only)

        emails = None

        # Strategy 1: Combined $search with KQL + boolean filters
        if kql:
            try:
                params = {
                    "$top": count,
                    "$select": EMAIL_SELECT_FIELDS,
                    "$search": f'"{kql}"',
                }
                response = await call_graph_api_paginated(
                    access_token, "GET", endpoint, params, count
                )
                emails = response.get("value", [])
                # Apply boolean filters client-side (can't combine $search and $filter)
                if boolean_filter and emails:
                    emails = _apply_client_filters(emails, has_attachments, unread_only)
            except GraphAPIError as e:
                logger.info(f"Combined search failed, trying fallback: {e}")

        # Strategy 2: Single-term search fallback
        if emails is None and kql:
            for term_key, term_val in [("subject", subject), ("from", from_addr), ("to", to), ("query", query)]:
                if not term_val:
                    continue
                try:
                    search_term = f"{term_key}:{term_val}" if term_key != "query" else term_val
                    params = {
                        "$top": count,
                        "$select": EMAIL_SELECT_FIELDS,
                        "$search": f'"{search_term}"',
                    }
                    response = await call_graph_api_paginated(
                        access_token, "GET", endpoint, params, count
                    )
                    emails = response.get("value", [])
                    if emails:
                        if boolean_filter:
                            emails = _apply_client_filters(emails, has_attachments, unread_only)
                        break
                except GraphAPIError:
                    continue

        # Strategy 3: Boolean filters only via $filter
        if emails is None and boolean_filter:
            try:
                params = {
                    "$top": count,
                    "$orderby": "receivedDateTime desc",
                    "$select": EMAIL_SELECT_FIELDS,
                    "$filter": boolean_filter,
                }
                response = await call_graph_api_paginated(
                    access_token, "GET", endpoint, params, count
                )
                emails = response.get("value", [])
            except GraphAPIError as e:
                logger.info(f"Filter search failed: {e}")

        # Strategy 4: Fallback — recent emails sorted by date
        if emails is None:
            params = {
                "$top": count,
                "$orderby": "receivedDateTime desc",
                "$select": EMAIL_SELECT_FIELDS,
            }
            response = await call_graph_api_paginated(
                access_token, "GET", endpoint, params, count
            )
            emails = response.get("value", [])

        if not emails:
            return f"No emails found matching your search criteria in {folder}."

        lines = []
        for i, email in enumerate(emails, 1):
            sender = email.get("from", {}).get("emailAddress", {})
            date = email.get("receivedDateTime", "")
            read_status = "" if email.get("isRead") else "[UNREAD] "

            lines.append(
                f"{i}. {read_status}{date}\n"
                f"   From: {sender.get('name', 'Unknown')} ({sender.get('address', '')})\n"
                f"   Subject: {email.get('subject', '(no subject)')}\n"
                f"   Preview: {email.get('bodyPreview', '')[:100]}\n"
                f"   ID: {email['id']}"
            )

        return f"Found {len(emails)} emails:\n\n" + "\n\n".join(lines)


def _apply_client_filters(
    emails: list[dict],
    has_attachments: bool | None,
    unread_only: bool,
) -> list[dict]:
    """Apply boolean filters client-side when $filter can't be used with $search."""
    result = emails
    if has_attachments is not None:
        result = [e for e in result if e.get("hasAttachments") == has_attachments]
    if unread_only:
        result = [e for e in result if not e.get("isRead")]
    return result
