#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  outlook-mcp Linux Build Script
#  Builds standalone executables for server and auth_server
# ============================================================

echo "============================================"
echo " outlook-mcp Linux Build"
echo "============================================"
echo ""

# -- Resolve paths --
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

# -- Verify source exists --
if [ ! -f "$SRC_DIR/server.py" ]; then
    echo "ERROR: Cannot find src/server.py. Run this script from the release/linux/ folder."
    exit 1
fi

# -- Install PyInstaller if not present --
echo "[1/5] Checking for PyInstaller..."
if python3 -m PyInstaller --version &>/dev/null; then
    echo "      PyInstaller is already installed."
else
    echo "      Installing PyInstaller..."
    pip3 install pyinstaller
fi

# -- Clean previous builds --
echo "[2/5] Cleaning previous build artifacts..."
rm -rf "$DIST_DIR" "$BUILD_DIR"

# -- Build server (MCP stdio server) --
echo "[3/5] Building server (MCP stdio server)..."
python3 -m PyInstaller \
    --name server \
    --onedir \
    --console \
    --paths "$SRC_DIR" \
    --hidden-import=config \
    --hidden-import=auth --hidden-import=auth.token_manager --hidden-import=auth.tools \
    --hidden-import=mail --hidden-import=mail.list_emails --hidden-import=mail.search_emails \
    --hidden-import=mail.read_email --hidden-import=mail.send_email --hidden-import=mail.draft_email \
    --hidden-import=mail.mark_as_read --hidden-import=mail.folder_utils \
    --hidden-import=cal --hidden-import=cal.list_events --hidden-import=cal.create_event \
    --hidden-import=cal.accept_event --hidden-import=cal.decline_event \
    --hidden-import=cal.cancel_event --hidden-import=cal.delete_event \
    --hidden-import=folder --hidden-import=folder.list_folders \
    --hidden-import=folder.create_folder --hidden-import=folder.move_emails \
    --hidden-import=rules --hidden-import=rules.list_rules \
    --hidden-import=rules.create_rule --hidden-import=rules.edit_rule_sequence \
    --hidden-import=utils --hidden-import=utils.graph_api \
    --hidden-import=utils.html_sanitizer --hidden-import=utils.mock_data \
    --hidden-import=dotenv --hidden-import=httpx --hidden-import=httpcore \
    --hidden-import=anyio --hidden-import=anyio._backends._asyncio \
    --hidden-import=sniffio --hidden-import=certifi --hidden-import=h11 --hidden-import=idna \
    --hidden-import=pydantic --hidden-import=mcp --hidden-import=mcp.server \
    --hidden-import=mcp.server.fastmcp --hidden-import=mcp.server.stdio \
    --hidden-import=mcp.types --hidden-import=mcp.shared \
    --distpath "$DIST_DIR/outlook-mcp-server" \
    --workpath "$BUILD_DIR/server" \
    --specpath "$BUILD_DIR" \
    --noconfirm \
    "$SRC_DIR/server.py"

# -- Build auth_server (Flask OAuth server) --
echo "[4/5] Building auth_server (Flask OAuth server)..."
python3 -m PyInstaller \
    --name auth_server \
    --onedir \
    --console \
    --paths "$SRC_DIR" \
    --hidden-import=config \
    --hidden-import=dotenv --hidden-import=httpx --hidden-import=httpcore \
    --hidden-import=anyio --hidden-import=sniffio --hidden-import=certifi \
    --hidden-import=h11 --hidden-import=idna \
    --hidden-import=flask --hidden-import=werkzeug --hidden-import=jinja2 \
    --hidden-import=markupsafe --hidden-import=click --hidden-import=itsdangerous \
    --hidden-import=blinker \
    --distpath "$DIST_DIR/outlook-mcp-auth" \
    --workpath "$BUILD_DIR/auth_server" \
    --specpath "$BUILD_DIR" \
    --noconfirm \
    "$SRC_DIR/auth_server.py"

# -- Copy .env.example alongside executables --
echo "[5/5] Copying .env.example to output directories..."
if [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$DIST_DIR/outlook-mcp-server/server/"
    cp "$ENV_EXAMPLE" "$DIST_DIR/outlook-mcp-auth/auth_server/"
    echo "      .env.example copied to both output directories."
else
    echo "      WARNING: .env.example not found at project root."
fi

echo ""
echo "============================================"
echo " Build Complete!"
echo "============================================"
echo ""
echo "Output directories:"
echo "  Server:      $DIST_DIR/outlook-mcp-server/server/"
echo "  Auth Server: $DIST_DIR/outlook-mcp-auth/auth_server/"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env in each output directory"
echo "  2. Edit .env with your Azure App Registration credentials"
echo "  3. Run ./server for the MCP server"
echo "  4. Run ./auth_server for the OAuth flow"
echo ""
