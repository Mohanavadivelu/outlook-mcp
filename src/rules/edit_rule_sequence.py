import urllib.parse
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api, call_graph_api_paginated


def register(mcp):
    @mcp.tool()
    async def edit_rule_sequence(rule_name: str, sequence: int) -> str:
        """Change the execution priority of an inbox rule.

        Lower sequence numbers execute first.

        Args:
            rule_name: Display name of the rule to update.
            sequence: New sequence number (priority). Lower = executes first.
        """
        access_token = await ensure_authenticated()

        # Find rule by name
        response = await call_graph_api_paginated(
            access_token, "GET", "me/mailFolders/inbox/messageRules", max_count=100
        )

        rules = response.get("value", [])
        target_rule = None
        for rule in rules:
            if rule.get("displayName", "").lower() == rule_name.lower():
                target_rule = rule
                break

        if not target_rule:
            available = [r.get("displayName", "(unnamed)") for r in rules]
            return (
                f"Rule '{rule_name}' not found.\n"
                f"Available rules: {', '.join(available) if available else '(none)'}"
            )

        rule_id = target_rule["id"]
        encoded_id = urllib.parse.quote(rule_id, safe="")

        await call_graph_api(
            access_token,
            "PATCH",
            f"me/mailFolders/inbox/messageRules/{encoded_id}",
            data={"sequence": sequence},
        )

        return (
            f"Rule '{rule_name}' sequence updated to {sequence}.\n"
            f"Rule ID: {rule_id}"
        )
