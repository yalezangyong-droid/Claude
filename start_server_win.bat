@echo off
REM ============================================================
REM LinkedIn Scraper - Windows 启动脚本 (使用 Cloudflare Tunnel)
REM ============================================================
REM
REM 首次使用前，请安装 cloudflared:
REM   winget install Cloudflare.cloudflared
REM
REM ============================================================

set GOOGLE_SHEET_ID=1Gv36EQuIC2E04E8dResLMa_K9xU6i1rc4Bubsi3FS1M
set GOOGLE_SHEET_NAME=Will's LinkedIn Automated Tracker
set GOOGLE_CREDENTIALS=credentials.json
set PORT=5000

echo ============================================================
echo LinkedIn Scraper Server (Cloudflare Tunnel)
echo ============================================================
echo.
echo Configuration:
echo   Sheet ID: %GOOGLE_SHEET_ID%
echo   Sheet Name: %GOOGLE_SHEET_NAME%
echo.
echo ============================================================
echo.
echo Starting Flask server...
echo.

python scraper_server.py --port %PORT% --sheet-id "%GOOGLE_SHEET_ID%" --sheet-name "%GOOGLE_SHEET_NAME%" --credentials "%GOOGLE_CREDENTIALS%"
