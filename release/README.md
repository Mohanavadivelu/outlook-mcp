# outlook-mcp Release Build

Build standalone executables for the outlook-mcp server so end users do not need
Python installed.

## Prerequisites

- **Python >= 3.10** (required at build time only, not at runtime)
- **pip** with access to PyPI (the build scripts install PyInstaller automatically)
- All project dependencies installed in the current Python environment:
  ```
  pip install mcp[cli] httpx python-dotenv flask
  ```

## Building

### Windows

```bat
cd release\windows
build.bat
```

Output appears in `release\windows\dist\`.

### Linux

```bash
cd release/linux
chmod +x build.sh
./build.sh
```

Output appears in `release/linux/dist/`.

## Output Structure

Each build produces two directories:

| Directory | Executable | Purpose |
|-----------|-----------|---------|
| `outlook-mcp-server/server/` | `server` (.exe on Windows) | MCP stdio server — connect this to your AI assistant |
| `outlook-mcp-auth/auth_server/` | `auth_server` (.exe on Windows) | OAuth HTTP server — run this to authenticate with Microsoft |

## Configuration

1. In each executable directory, rename `.env.example` to `.env`.
2. Fill in your Azure App Registration credentials:
   - `MS_CLIENT_ID` — your Application (client) ID
   - `MS_CLIENT_SECRET` — your client secret value
   - `MS_TENANT_ID` — your tenant ID (or `common` for multi-tenant)
3. The `.env` file **must** be in the same directory as the executable, or in the
   current working directory when you launch the executable.

## Usage

### Step 1: Authenticate

Run the auth server and open your browser:

```bash
# Start the auth server
./auth_server        # Linux
auth_server.exe      # Windows

# Then open http://localhost:3333/auth in your browser
```

### Step 2: Run the MCP Server

Once authenticated, start the MCP server. Configure your AI assistant to launch it:

```json
{
  "mcpServers": {
    "outlook": {
      "command": "/path/to/outlook-mcp-server/server/server"
    }
  }
}
```

On Windows, use the full path to `server.exe`.

## Token Storage

Authentication tokens are stored at `~/.outlook-mcp-tokens.json` by default.
Override this with the `TOKEN_STORE_PATH` environment variable in your `.env` file.

## Troubleshooting

- **Missing modules at runtime**: If PyInstaller misses a dependency, add it as
  `--hidden-import=module_name` in the build script.
- **`.env` not found**: Ensure the `.env` file is in the same folder as the
  executable, or set environment variables directly.
- **Cross-platform builds**: PyInstaller cannot cross-compile. Build on the
  target OS (Windows builds on Windows, Linux builds on Linux).
- **Python 3.14+**: PyInstaller may not support the latest Python. Use Python 3.12
  or 3.13 if the build fails.
