@echo off
echo ============================================================
echo LinkedIn Scraper Server
echo ============================================================
echo.

REM Set your configuration here
set GOOGLE_SHEET_ID=1Gv36EQuIC2E04E8dResLMa_K9xU6i1rc4Bubsi3FS1M
set GOOGLE_SHEET_NAME=Will's LinkedIn Automated Tracker
set GOOGLE_CREDENTIALS=credentials.json

echo Starting server with configuration:
echo   Sheet ID: %GOOGLE_SHEET_ID%
echo   Sheet Name: %GOOGLE_SHEET_NAME%
echo   Credentials: %GOOGLE_CREDENTIALS%
echo.
echo Server will start on http://localhost:5000
echo.
echo To expose to internet:
echo   1. Download ngrok from https://ngrok.com/download
echo   2. Open another terminal and run: ngrok http 5000
echo   3. Use the ngrok URL in Google Apps Script
echo.
echo ============================================================

python scraper_server.py --port 5000 --sheet-id "%GOOGLE_SHEET_ID%" --sheet-name "%GOOGLE_SHEET_NAME%" --credentials "%GOOGLE_CREDENTIALS%"

pause
