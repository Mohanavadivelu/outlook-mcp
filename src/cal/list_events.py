from datetime import datetime, timezone
from config import CALENDAR_SELECT_FIELDS, MAX_RESULT_COUNT
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api_paginated


def register(mcp):
    @mcp.tool()
    async def list_events(count: int = 10) -> str:
        """List upcoming calendar events starting from now.

        Args:
            count: Number of events to retrieve (default: 10, max: 50).
        """
        access_token = await ensure_authenticated()
        count = min(count, MAX_RESULT_COUNT)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        query_params = {
            "$top": count,
            "$orderby": "start/dateTime",
            "$select": CALENDAR_SELECT_FIELDS,
            "$filter": f"start/dateTime ge '{now}'",
        }

        response = await call_graph_api_paginated(
            access_token, "GET", "me/events", query_params, count
        )

        events = response.get("value", [])
        if not events:
            return "No upcoming events found."

        lines = []
        for i, event in enumerate(events, 1):
            start = event.get("start", {})
            end = event.get("end", {})
            location = event.get("location", {}).get("displayName", "No location")
            organizer = event.get("organizer", {}).get("emailAddress", {})

            attendee_names = [
                a.get("emailAddress", {}).get("name", a.get("emailAddress", {}).get("address", ""))
                for a in event.get("attendees", [])
            ]

            status = ""
            if event.get("isCancelled"):
                status = "[CANCELLED] "
            if event.get("isAllDay"):
                status += "[ALL DAY] "

            lines.append(
                f"{i}. {status}{event.get('subject', '(no subject)')}\n"
                f"   Start: {start.get('dateTime', '')} ({start.get('timeZone', '')})\n"
                f"   End: {end.get('dateTime', '')} ({end.get('timeZone', '')})\n"
                f"   Location: {location}\n"
                f"   Organizer: {organizer.get('name', '')} ({organizer.get('address', '')})\n"
                + (f"   Attendees: {', '.join(attendee_names)}\n" if attendee_names else "")
                + f"   ID: {event['id']}"
            )

        return f"Found {len(events)} upcoming events:\n\n" + "\n\n".join(lines)
