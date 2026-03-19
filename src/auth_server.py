"""Standalone OAuth HTTP server for handling Microsoft auth redirects.

This is a separate process from the MCP stdio server.
Run it with: python auth_server.py
"""

import json
import secrets
import time
import logging
import sys
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, redirect, request, jsonify

from config import (
    MS_CLIENT_ID,
    MS_CLIENT_SECRET,
    MS_TENANT_ID,
    MS_REDIRECT_URI,
    OAUTH_SCOPES,
    TOKEN_STORE_PATH,
)

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("outlook-mcp-auth")

app = Flask(__name__)

# Store state parameter for CSRF validation
_pending_states: dict[str, float] = {}

AUTH_ENDPOINT = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"


@app.route("/auth")
def auth():
    """Build Microsoft OAuth authorize URL and redirect the browser."""
    state = secrets.token_urlsafe(32)
    _pending_states[state] = time.time()

    # Clean up old states (older than 10 minutes)
    cutoff = time.time() - 600
    stale = [s for s, t in _pending_states.items() if t < cutoff]
    for s in stale:
        del _pending_states[s]

    params = {
        "client_id": MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": MS_REDIRECT_URI,
        "scope": " ".join(OAUTH_SCOPES),
        "response_mode": "query",
        "state": state,
    }

    url = f"{AUTH_ENDPOINT}?{urlencode(params)}"
    logger.info(f"Redirecting to Microsoft login (state={state[:8]}...)")
    return redirect(url)


@app.route("/auth/callback")
def auth_callback():
    """Receive auth code from Microsoft, exchange for tokens, save to file."""
    error = request.args.get("error")
    if error:
        error_desc = request.args.get("error_description", "Unknown error")
        logger.error(f"OAuth error: {error} - {error_desc}")
        return f"<h2>Authentication Failed</h2><p>{error}: {error_desc}</p>", 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "<h2>Error</h2><p>No authorization code received.</p>", 400

    # Validate state for CSRF protection
    if state not in _pending_states:
        logger.warning("Invalid or expired state parameter")
        return "<h2>Error</h2><p>Invalid state parameter. Please try authenticating again.</p>", 400

    del _pending_states[state]

    # Exchange authorization code for tokens
    import httpx

    token_data = {
        "client_id": MS_CLIENT_ID,
        "client_secret": MS_CLIENT_SECRET,
        "code": code,
        "redirect_uri": MS_REDIRECT_URI,
        "grant_type": "authorization_code",
        "scope": " ".join(OAUTH_SCOPES),
    }

    try:
        response = httpx.post(TOKEN_ENDPOINT, data=token_data, timeout=30.0)

        if response.status_code != 200:
            logger.error(f"Token exchange failed ({response.status_code}): {response.text}")
            return f"<h2>Token Exchange Failed</h2><pre>{response.text}</pre>", 500

        tokens = response.json()

        # Add absolute expiry timestamp (milliseconds)
        expires_in = tokens.get("expires_in", 3600)
        tokens["expires_at"] = int((time.time() + expires_in) * 1000)

        # Save tokens to file
        TOKEN_STORE_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
        logger.info("Tokens saved successfully")

        return (
            "<h2>Authentication Successful!</h2>"
            "<p>You can close this browser tab and return to your AI assistant.</p>"
            "<p>The MCP server is now authenticated with Microsoft Outlook.</p>"
        )

    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return f"<h2>Error</h2><p>{e}</p>", 500


@app.route("/token-status")
def token_status():
    """Return current token validity status."""
    try:
        if not TOKEN_STORE_PATH.exists():
            return jsonify({"authenticated": False, "reason": "No token file found"})

        tokens = json.loads(TOKEN_STORE_PATH.read_text(encoding="utf-8"))
        expires_at = tokens.get("expires_at", 0)
        now_ms = int(time.time() * 1000)

        if now_ms >= expires_at:
            return jsonify({
                "authenticated": False,
                "reason": "Access token expired",
                "has_refresh_token": bool(tokens.get("refresh_token")),
            })

        return jsonify({
            "authenticated": True,
            "expires_in_seconds": (expires_at - now_ms) // 1000,
        })

    except Exception as e:
        return jsonify({"authenticated": False, "reason": str(e)}), 500


if __name__ == "__main__":
    if not MS_CLIENT_ID:
        logger.error("MS_CLIENT_ID (or OUTLOOK_CLIENT_ID) is not set. Check your .env file.")
        sys.exit(1)

    logger.info(f"Starting OAuth auth server on http://localhost:3333")
    logger.info(f"Redirect URI: {MS_REDIRECT_URI}")
    logger.info(f"Token store: {TOKEN_STORE_PATH}")
    app.run(host="localhost", port=3333, debug=False)
