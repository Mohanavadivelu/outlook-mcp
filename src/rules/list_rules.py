from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api_paginated


def register(mcp):
    @mcp.tool()
    async def list_rules(include_details: bool = False) -> str:
        """List all inbox message rules.

        Args:
            include_details: Show full rule conditions and actions. Default: False.
        """
        access_token = await ensure_authenticated()

        response = await call_graph_api_paginated(
            access_token, "GET", "me/mailFolders/inbox/messageRules", max_count=100
        )

        rules = response.get("value", [])
        if not rules:
            return "No inbox rules found."

        lines = []
        for i, rule in enumerate(rules, 1):
            name = rule.get("displayName", "(unnamed)")
            enabled = "Enabled" if rule.get("isEnabled") else "Disabled"
            sequence = rule.get("sequence", "?")

            line = f"{i}. {name} [{enabled}] (priority: {sequence})"

            if include_details:
                conditions = rule.get("conditions", {})
                actions = rule.get("actions", {})

                # Format conditions
                cond_parts = []
                from_addrs = conditions.get("fromAddresses", [])
                if from_addrs:
                    addrs = [a.get("emailAddress", {}).get("address", "") for a in from_addrs]
                    cond_parts.append(f"From: {', '.join(addrs)}")

                subject_contains = conditions.get("subjectContains", [])
                if subject_contains:
                    cond_parts.append(f"Subject contains: {', '.join(subject_contains)}")

                if conditions.get("hasAttachment") is not None:
                    cond_parts.append(f"Has attachments: {conditions['hasAttachment']}")

                # Format actions
                action_parts = []
                if actions.get("moveToFolder"):
                    action_parts.append(f"Move to folder: {actions['moveToFolder']}")
                if actions.get("markAsRead"):
                    action_parts.append("Mark as read")
                if actions.get("delete"):
                    action_parts.append("Delete")
                if actions.get("forwardTo"):
                    fwd = [a.get("emailAddress", {}).get("address", "") for a in actions["forwardTo"]]
                    action_parts.append(f"Forward to: {', '.join(fwd)}")

                if cond_parts:
                    line += f"\n   Conditions: {'; '.join(cond_parts)}"
                if action_parts:
                    line += f"\n   Actions: {'; '.join(action_parts)}"

            line += f"\n   Rule ID: {rule.get('id', '')}"
            lines.append(line)

        return f"Inbox rules ({len(rules)}):\n\n" + "\n\n".join(lines)
