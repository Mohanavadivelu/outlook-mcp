from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api
from mail.folder_utils import resolve_folder_id


def register(mcp):
    @mcp.tool()
    async def create_rule(
        name: str,
        from_addresses: str = "",
        contains_subject: str = "",
        has_attachments: bool | None = None,
        move_to_folder: str = "",
        mark_as_read: bool = False,
        is_enabled: bool = True,
        sequence: int = 0,
    ) -> str:
        """Create a new inbox message rule.

        Args:
            name: Display name for the rule.
            from_addresses: Comma-separated sender email addresses to match.
            contains_subject: Comma-separated subject keywords to match.
            has_attachments: Match emails with/without attachments (True/False/None to ignore).
            move_to_folder: Folder name or ID to move matching emails to.
            mark_as_read: Mark matching emails as read. Default: False.
            is_enabled: Whether the rule is enabled. Default: True.
            sequence: Rule execution priority (lower = higher priority). 0 = auto.
        """
        access_token = await ensure_authenticated()

        # Build conditions
        conditions = {}

        if from_addresses:
            conditions["fromAddresses"] = [
                {"emailAddress": {"address": addr.strip()}}
                for addr in from_addresses.split(",")
                if addr.strip()
            ]

        if contains_subject:
            conditions["subjectContains"] = [
                s.strip() for s in contains_subject.split(",") if s.strip()
            ]

        if has_attachments is not None:
            conditions["hasAttachments"] = has_attachments

        if not conditions:
            return "Error: At least one condition is required (from_addresses, contains_subject, or has_attachments)."

        # Build actions
        actions = {}

        if move_to_folder:
            folder_id = await resolve_folder_id(access_token, move_to_folder)
            actions["moveToFolder"] = folder_id

        if mark_as_read:
            actions["markAsRead"] = True

        if not actions:
            return "Error: At least one action is required (move_to_folder or mark_as_read)."

        rule_data = {
            "displayName": name,
            "isEnabled": is_enabled,
            "conditions": conditions,
            "actions": actions,
        }

        if sequence > 0:
            rule_data["sequence"] = sequence

        result = await call_graph_api(
            access_token, "POST", "me/mailFolders/inbox/messageRules", data=rule_data
        )

        rule_id = result.get("id", "unknown")
        return (
            f"Rule created successfully.\n"
            f"Name: {name}\n"
            f"Enabled: {is_enabled}\n"
            f"Rule ID: {rule_id}"
        )
