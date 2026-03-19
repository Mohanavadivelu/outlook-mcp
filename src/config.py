import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Server identity
SERVER_NAME = "outlook-mcp"
SERVER_VERSION = "1.0.0"

# Microsoft Graph API
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/"

# Azure App Registration — support both env var naming conventions
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID") or os.getenv("OUTLOOK_CLIENT_ID", "")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET") or os.getenv("OUTLOOK_CLIENT_SECRET", "")
MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:3333/auth/callback")

# OAuth scopes
OAUTH_SCOPES = [
    "offline_access",
    "User.Read",
    "Mail.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.Read",
    "Calendars.ReadWrite",
]

MS_SCOPES_STR = os.getenv("MS_SCOPES")
if MS_SCOPES_STR:
    OAUTH_SCOPES = MS_SCOPES_STR.split(" ")

# Token storage
TOKEN_STORE_PATH = Path(os.getenv("TOKEN_STORE_PATH", Path.home() / ".outlook-mcp-tokens.json"))

# Auth server
AUTH_SERVER_URL = "http://localhost:3333"

# Pagination defaults
DEFAULT_PAGE_SIZE = 25
MAX_RESULT_COUNT = 50

# Timezone
DEFAULT_TIMEZONE = "Central European Standard Time"

# OData $select field lists
EMAIL_SELECT_FIELDS = (
    "id,subject,from,toRecipients,ccRecipients,"
    "receivedDateTime,bodyPreview,hasAttachments,importance,isRead"
)
EMAIL_DETAIL_FIELDS = (
    "id,subject,from,toRecipients,ccRecipients,bccRecipients,"
    "receivedDateTime,bodyPreview,body,hasAttachments,importance,isRead,internetMessageHeaders"
)
CALENDAR_SELECT_FIELDS = (
    "id,subject,bodyPreview,start,end,location,organizer,attendees,isAllDay,isCancelled"
)

# Test mode
USE_TEST_MODE = os.getenv("USE_TEST_MODE", "false").lower() == "true"
