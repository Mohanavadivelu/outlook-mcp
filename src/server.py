import logging
import sys
from mcp.server.fastmcp import FastMCP
from config import SERVER_NAME

# Configure logging to stderr (CRITICAL for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(SERVER_NAME)

# Initialize FastMCP server
mcp = FastMCP(SERVER_NAME)

# Register all tool modules
from auth.tools import register_tools as register_auth_tools
from mail import register_tools as register_email_tools
from cal import register_tools as register_calendar_tools
from folder import register_tools as register_folder_tools
from rules import register_tools as register_rules_tools

register_auth_tools(mcp)
register_email_tools(mcp)
register_calendar_tools(mcp)
register_folder_tools(mcp)
register_rules_tools(mcp)


def main():
    logger.info(f"Starting {SERVER_NAME} MCP server (stdio transport)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
