from config import DEFAULT_TIMEZONE
from auth.token_manager import ensure_authenticated
from utils.graph_api import call_graph_api


def register(mcp):
    @mcp.tool()
    async def create_event(
        subject: str,
        start: str,
        end: str,
        attendees: str = "",
        body: str = "",
        location: str = "",
        is_all_day: bool = False,
        timezone: str = "",
    ) -> str:
        """Create a new calendar event.

        Args:
            subject: Event title/subject.
            start: Start date-time in ISO 8601 format (e.g., '2025-01-20T10:00:00').
            end: End date-time in ISO 8601 format (e.g., '2025-01-20T11:00:00').
            attendees: Comma-separated email addresses of attendees.
            body: Event description/body text.
            location: Event location.
            is_all_day: Whether this is an all-day event. Default: False.
            timezone: Timezone for the event (e.g., 'Central European Standard Time'). Uses server default if not specified.
        """
        access_token = await ensure_authenticated()

        tz = timezone or DEFAULT_TIMEZONE

        event_data = {
            "subject": subject,
            "start": {"dateTime": start, "timeZone": tz},
            "end": {"dateTime": end, "timeZone": tz},
            "isAllDay": is_all_day,
        }

        if body:
            event_data["body"] = {"contentType": "Text", "content": body}

        if location:
            event_data["location"] = {"displayName": location}

        if attendees:
            event_data["attendees"] = [
                {
                    "emailAddress": {"address": addr.strip()},
                    "type": "required",
                }
                for addr in attendees.split(",")
                if addr.strip()
            ]

        result = await call_graph_api(access_token, "POST", "me/events", data=event_data)

        event_id = result.get("id", "unknown")
        return (
            f"Event created successfully.\n"
            f"Subject: {subject}\n"
            f"Start: {start} ({tz})\n"
            f"End: {end} ({tz})\n"
            f"Event ID: {event_id}"
        )
