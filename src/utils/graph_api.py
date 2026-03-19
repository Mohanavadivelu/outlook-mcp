import logging
import httpx
from config import GRAPH_API_ENDPOINT, USE_TEST_MODE

logger = logging.getLogger("outlook-mcp")


class GraphAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Graph API error ({status_code}): {message}")


class UnauthorizedError(GraphAPIError):
    def __init__(self, message: str = "Access token is invalid or expired"):
        super().__init__(401, message)


async def call_graph_api(
    access_token: str,
    method: str,
    path: str,
    data: dict = None,
    query_params: dict = None,
) -> dict:
    """Make a single request to the Microsoft Graph API.

    Args:
        access_token: Valid OAuth access token.
        method: HTTP method (GET, POST, PATCH, DELETE).
        path: API path (e.g. "me/messages") or full URL for pagination.
        data: Request body for POST/PATCH.
        query_params: OData query parameters.

    Returns:
        Parsed JSON response dict.
    """
    if USE_TEST_MODE:
        from utils.mock_data import get_mock_response
        return get_mock_response(method, path, data, query_params)

    # Support full URLs (pagination @odata.nextLink)
    if path.startswith("https://"):
        url = path
    else:
        url = f"{GRAPH_API_ENDPOINT}{path}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            params=query_params,
        )

    if response.status_code == 401:
        raise UnauthorizedError()

    if response.status_code == 204:
        return {}

    if response.status_code >= 400:
        try:
            error_body = response.json()
            message = error_body.get("error", {}).get("message", response.text)
        except Exception:
            message = response.text
        raise GraphAPIError(response.status_code, message)

    if not response.text:
        return {}

    return response.json()


async def call_graph_api_paginated(
    access_token: str,
    method: str,
    path: str,
    query_params: dict = None,
    max_count: int = 0,
) -> dict:
    """Make paginated requests, following @odata.nextLink.

    Args:
        access_token: Valid OAuth access token.
        method: HTTP method.
        path: API path.
        query_params: OData query parameters.
        max_count: Maximum items to collect. 0 = use single page only.

    Returns:
        Dict with "value" key containing all collected items.
    """
    all_items = []
    current_path = path
    current_params = query_params

    while True:
        response = await call_graph_api(
            access_token, method, current_path, query_params=current_params
        )

        items = response.get("value", [])
        all_items.extend(items)

        if max_count and len(all_items) >= max_count:
            all_items = all_items[:max_count]
            break

        next_link = response.get("@odata.nextLink")
        if not next_link:
            break

        # Next link is a full URL — params are embedded in it
        current_path = next_link
        current_params = None

    return {"value": all_items}
