"""Mock responses for test mode (USE_TEST_MODE=true)."""

import logging

logger = logging.getLogger("outlook-mcp")

MOCK_EMAILS = {
    "value": [
        {
            "id": "mock-email-001",
            "subject": "Weekly Team Standup Notes",
            "from": {"emailAddress": {"name": "Alice Johnson", "address": "alice@example.com"}},
            "toRecipients": [{"emailAddress": {"name": "Team", "address": "team@example.com"}}],
            "ccRecipients": [],
            "receivedDateTime": "2025-01-15T09:30:00Z",
            "bodyPreview": "Here are the notes from today's standup meeting...",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": True,
        },
        {
            "id": "mock-email-002",
            "subject": "Project Deadline Reminder",
            "from": {"emailAddress": {"name": "Bob Smith", "address": "bob@example.com"}},
            "toRecipients": [{"emailAddress": {"name": "You", "address": "you@example.com"}}],
            "ccRecipients": [],
            "receivedDateTime": "2025-01-15T14:00:00Z",
            "bodyPreview": "Just a reminder that the project deadline is next Friday...",
            "hasAttachments": True,
            "importance": "high",
            "isRead": False,
        },
        {
            "id": "mock-email-003",
            "subject": "Lunch plans?",
            "from": {"emailAddress": {"name": "Carol Davis", "address": "carol@example.com"}},
            "toRecipients": [{"emailAddress": {"name": "You", "address": "you@example.com"}}],
            "ccRecipients": [],
            "receivedDateTime": "2025-01-15T11:45:00Z",
            "bodyPreview": "Hey, want to grab lunch today? Thinking about that new place...",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": True,
        },
    ]
}

MOCK_EMAIL_DETAIL = {
    "id": "mock-email-001",
    "subject": "Weekly Team Standup Notes",
    "from": {"emailAddress": {"name": "Alice Johnson", "address": "alice@example.com"}},
    "toRecipients": [{"emailAddress": {"name": "Team", "address": "team@example.com"}}],
    "ccRecipients": [],
    "bccRecipients": [],
    "receivedDateTime": "2025-01-15T09:30:00Z",
    "bodyPreview": "Here are the notes from today's standup meeting...",
    "body": {
        "contentType": "html",
        "content": "<html><body><p>Here are the notes from today's standup meeting.</p>"
        "<ul><li>Alice: Working on auth module</li>"
        "<li>Bob: Finishing API integration</li>"
        "<li>Carol: Code review backlog</li></ul></body></html>",
    },
    "hasAttachments": False,
    "importance": "normal",
    "isRead": True,
    "internetMessageHeaders": [],
}

MOCK_EVENTS = {
    "value": [
        {
            "id": "mock-event-001",
            "subject": "Sprint Planning",
            "bodyPreview": "Review backlog and plan next sprint",
            "start": {"dateTime": "2025-01-20T10:00:00", "timeZone": "Central European Standard Time"},
            "end": {"dateTime": "2025-01-20T11:00:00", "timeZone": "Central European Standard Time"},
            "location": {"displayName": "Conference Room A"},
            "organizer": {"emailAddress": {"name": "Alice Johnson", "address": "alice@example.com"}},
            "attendees": [
                {"emailAddress": {"name": "Bob Smith", "address": "bob@example.com"}, "type": "required"},
            ],
            "isAllDay": False,
            "isCancelled": False,
        },
        {
            "id": "mock-event-002",
            "subject": "1:1 with Manager",
            "bodyPreview": "Weekly sync",
            "start": {"dateTime": "2025-01-20T14:00:00", "timeZone": "Central European Standard Time"},
            "end": {"dateTime": "2025-01-20T14:30:00", "timeZone": "Central European Standard Time"},
            "location": {"displayName": "Virtual - Teams"},
            "organizer": {"emailAddress": {"name": "Manager", "address": "manager@example.com"}},
            "attendees": [],
            "isAllDay": False,
            "isCancelled": False,
        },
    ]
}

MOCK_FOLDERS = {
    "value": [
        {"id": "folder-inbox", "displayName": "Inbox", "totalItemCount": 142, "unreadItemCount": 5},
        {"id": "folder-drafts", "displayName": "Drafts", "totalItemCount": 3, "unreadItemCount": 0},
        {"id": "folder-sent", "displayName": "Sent Items", "totalItemCount": 89, "unreadItemCount": 0},
        {"id": "folder-deleted", "displayName": "Deleted Items", "totalItemCount": 12, "unreadItemCount": 0},
        {"id": "folder-junk", "displayName": "Junk Email", "totalItemCount": 7, "unreadItemCount": 2},
        {"id": "folder-archive", "displayName": "Archive", "totalItemCount": 234, "unreadItemCount": 0},
    ]
}

MOCK_RULES = {
    "value": [
        {
            "id": "rule-001",
            "displayName": "Move GitHub Emails",
            "isEnabled": True,
            "sequence": 1,
            "conditions": {
                "fromAddresses": [{"emailAddress": {"address": "notifications@github.com"}}],
            },
            "actions": {
                "moveToFolder": "folder-github",
                "markAsRead": True,
            },
        },
    ]
}

MOCK_SUCCESS = {"status": "success"}


def get_mock_response(method: str, path: str, data: dict = None, query_params: dict = None) -> dict:
    """Return mock data based on the API path."""
    logger.info(f"[TEST MODE] {method} {path}")

    path_lower = path.lower() if path else ""

    # Email detail
    if "/messages/" in path_lower and method.upper() == "GET" and not path_lower.endswith("/messages"):
        return MOCK_EMAIL_DETAIL

    # Email list / search
    if "messages" in path_lower and method.upper() == "GET":
        return MOCK_EMAILS

    # Send mail
    if "sendmail" in path_lower:
        return MOCK_SUCCESS

    # Events
    if "events" in path_lower and method.upper() == "GET":
        return MOCK_EVENTS

    # Event create
    if "events" in path_lower and method.upper() == "POST":
        return {"id": "mock-event-new", "subject": data.get("subject", "New Event") if data else "New Event"}

    # Folders
    if "mailfolders" in path_lower and method.upper() == "GET":
        return MOCK_FOLDERS

    # Folder create
    if "mailfolders" in path_lower and method.upper() == "POST":
        return {"id": "folder-new", "displayName": data.get("displayName", "New Folder") if data else "New Folder"}

    # Rules
    if "messagerules" in path_lower and method.upper() == "GET":
        return MOCK_RULES

    # Move / PATCH / DELETE / other POST
    if method.upper() in ("POST", "PATCH", "DELETE"):
        return MOCK_SUCCESS

    return MOCK_SUCCESS
