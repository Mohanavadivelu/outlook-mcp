import json
import time
import logging
import httpx
from config import TOKEN_STORE_PATH, MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT_ID, MS_REDIRECT_URI, OAUTH_SCOPES

logger = logging.getLogger("outlook-mcp")

# In-memory cache
_cached_tokens: dict | None = None


class AuthenticationRequiredError(Exception):
    pass


def load_tokens() -> dict | None:
    """Read and parse tokens from the JSON file."""
    try:
        if TOKEN_STORE_PATH.exists():
            data = json.loads(TOKEN_STORE_PATH.read_text(encoding="utf-8"))
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load tokens: {e}")
    return None


def save_tokens(tokens: dict) -> None:
    """Write tokens dict to JSON file."""
    global _cached_tokens
    try:
        TOKEN_STORE_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
        _cached_tokens = tokens
        logger.info("Tokens saved successfully")
    except OSError as e:
        logger.error(f"Failed to save tokens: {e}")
        raise


def get_access_token() -> str | None:
    """Return cached token or load from file. None if missing or expired."""
    global _cached_tokens
    tokens = _cached_tokens or load_tokens()
    if not tokens:
        return None

    _cached_tokens = tokens
    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at", 0)

    # Check expiry with 5-minute buffer
    if expires_at and time.time() * 1000 >= expires_at - 300_000:
        return None

    return access_token


async def refresh_access_token() -> str | None:
    """Use refresh_token to get a new access_token from Microsoft."""
    global _cached_tokens
    tokens = _cached_tokens or load_tokens()
    if not tokens or not tokens.get("refresh_token"):
        return None

    token_url = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "client_id": MS_CLIENT_ID,
        "client_secret": MS_CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"],
        "grant_type": "refresh_token",
        "redirect_uri": MS_REDIRECT_URI,
        "scope": " ".join(OAUTH_SCOPES),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=payload)

        if response.status_code != 200:
            logger.error(f"Token refresh failed ({response.status_code}): {response.text}")
            return None

        new_tokens = response.json()
        # Calculate absolute expiry timestamp in milliseconds
        expires_in = new_tokens.get("expires_in", 3600)
        new_tokens["expires_at"] = int((time.time() + expires_in) * 1000)

        save_tokens(new_tokens)
        return new_tokens.get("access_token")

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return None


async def get_valid_access_token() -> str | None:
    """Load tokens → check expiry → refresh if needed → return valid token or None."""
    token = get_access_token()
    if token:
        return token

    # Try refreshing
    logger.info("Access token expired or missing, attempting refresh...")
    token = await refresh_access_token()
    return token


async def ensure_authenticated() -> str:
    """Returns a valid access token or raises AuthenticationRequiredError."""
    token = await get_valid_access_token()
    if not token:
        raise AuthenticationRequiredError(
            "Authentication required. Use the 'authenticate' tool first."
        )
    return token
