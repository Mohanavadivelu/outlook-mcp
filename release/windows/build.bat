@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM  outlook-mcp Windows Build Script
REM  Builds standalone executables for server.exe and auth_server.exe
REM ============================================================

echo ============================================
echo  outlook-mcp Windows Build
echo ============================================
echo.

REM -- Resolve paths --
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "SRC_DIR=%PROJECT_ROOT%\src"
set "DIST_DIR=%SCRIPT_DIR%dist"
set "BUILD_DIR=%SCRIPT_DIR%build"
set "ENV_EXAMPLE=%PROJECT_ROOT%\.env.example"

REM -- Verify source exists --
if not exist "%SRC_DIR%\server.py" (
    echo ERROR: Cannot find src\server.py. Run this script from the release\windows\ folder.
    exit /b 1
)

REM -- Install PyInstaller if not present --
echo [1/5] Checking for PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo       Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller.
        exit /b 1
    )
) else (
    echo       PyInstaller is already installed.
)

REM -- Clean previous builds --
echo [2/5] Cleaning previous build artifacts...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

REM -- Build server.exe (MCP stdio server) --
echo [3/5] Building server.exe (MCP stdio server)...
python -m PyInstaller ^
    --name server ^
    --onedir ^
    --console ^
    --paths "%SRC_DIR%" ^
    --hidden-import=config ^
    --hidden-import=auth --hidden-import=auth.token_manager --hidden-import=auth.tools ^
    --hidden-import=mail --hidden-import=mail.list_emails --hidden-import=mail.search_emails ^
    --hidden-import=mail.read_email --hidden-import=mail.send_email --hidden-import=mail.draft_email ^
    --hidden-import=mail.mark_as_read --hidden-import=mail.folder_utils ^
    --hidden-import=cal --hidden-import=cal.list_events --hidden-import=cal.create_event ^
    --hidden-import=cal.accept_event --hidden-import=cal.decline_event ^
    --hidden-import=cal.cancel_event --hidden-import=cal.delete_event ^
    --hidden-import=folder --hidden-import=folder.list_folders ^
    --hidden-import=folder.create_folder --hidden-import=folder.move_emails ^
    --hidden-import=rules --hidden-import=rules.list_rules ^
    --hidden-import=rules.create_rule --hidden-import=rules.edit_rule_sequence ^
    --hidden-import=utils --hidden-import=utils.graph_api ^
    --hidden-import=utils.html_sanitizer --hidden-import=utils.mock_data ^
    --hidden-import=dotenv --hidden-import=httpx --hidden-import=httpcore ^
    --hidden-import=anyio --hidden-import=anyio._backends._asyncio ^
    --hidden-import=sniffio --hidden-import=certifi --hidden-import=h11 --hidden-import=idna ^
    --hidden-import=pydantic --hidden-import=mcp --hidden-import=mcp.server ^
    --hidden-import=mcp.server.fastmcp --hidden-import=mcp.server.stdio ^
    --hidden-import=mcp.types --hidden-import=mcp.shared ^
    --distpath "%DIST_DIR%\outlook-mcp-server" ^
    --workpath "%BUILD_DIR%\server" ^
    --specpath "%BUILD_DIR%" ^
    --noconfirm ^
    "%SRC_DIR%\server.py"

if errorlevel 1 (
    echo ERROR: server.exe build failed.
    exit /b 1
)

REM -- Build auth_server.exe (Flask OAuth server) --
echo [4/5] Building auth_server.exe (Flask OAuth server)...
python -m PyInstaller ^
    --name auth_server ^
    --onedir ^
    --console ^
    --paths "%SRC_DIR%" ^
    --hidden-import=config ^
    --hidden-import=dotenv --hidden-import=httpx --hidden-import=httpcore ^
    --hidden-import=anyio --hidden-import=sniffio --hidden-import=certifi ^
    --hidden-import=h11 --hidden-import=idna ^
    --hidden-import=flask --hidden-import=werkzeug --hidden-import=jinja2 ^
    --hidden-import=markupsafe --hidden-import=click --hidden-import=itsdangerous ^
    --hidden-import=blinker ^
    --distpath "%DIST_DIR%\outlook-mcp-auth" ^
    --workpath "%BUILD_DIR%\auth_server" ^
    --specpath "%BUILD_DIR%" ^
    --noconfirm ^
    "%SRC_DIR%\auth_server.py"

if errorlevel 1 (
    echo ERROR: auth_server.exe build failed.
    exit /b 1
)

REM -- Copy .env.example alongside executables --
echo [5/5] Copying .env.example to output directories...
if exist "%ENV_EXAMPLE%" (
    copy "%ENV_EXAMPLE%" "%DIST_DIR%\outlook-mcp-server\server\" >nul
    copy "%ENV_EXAMPLE%" "%DIST_DIR%\outlook-mcp-auth\auth_server\" >nul
    echo       .env.example copied to both output directories.
) else (
    echo       WARNING: .env.example not found at project root.
)

echo.
echo ============================================
echo  Build Complete!
echo ============================================
echo.
echo Output directories:
echo   Server:      %DIST_DIR%\outlook-mcp-server\server\
echo   Auth Server: %DIST_DIR%\outlook-mcp-auth\auth_server\
echo.
echo Next steps:
echo   1. Copy .env.example to .env in each output directory
echo   2. Edit .env with your Azure App Registration credentials
echo   3. Run server.exe for the MCP server
echo   4. Run auth_server.exe for the OAuth flow
echo.

endlocal
