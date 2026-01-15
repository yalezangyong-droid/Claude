@echo off
REM ============================================================
REM LinkedIn Scraper - Cloudflare Tunnel 启动脚本
REM ============================================================
REM
REM 这个脚本启动 Cloudflare Tunnel
REM 请先在另一个窗口运行 start_server_win.bat
REM
REM ============================================================

set PORT=5000

echo ============================================================
echo Starting Cloudflare Tunnel...
echo ============================================================
echo.
echo 等待下面显示的 URL (类似 https://xxxxx.trycloudflare.com)
echo 复制这个 URL 到 Google Apps Script 的 SCRAPER_URL
echo.
echo ============================================================
echo.

cloudflared tunnel --url http://localhost:%PORT%
