#!/bin/bash
# ============================================================
# LinkedIn Scraper - Start Both Server and Cloudflare Tunnel
# ============================================================
# This script starts both Flask server and Cloudflare Tunnel
# ============================================================

PORT=5000

echo "============================================================"
echo "LinkedIn Scraper - Full Stack Startup"
echo "============================================================"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "ERROR: cloudflared not found!"
    echo ""
    echo "Please install cloudflared first:"
    echo "  Mac:   brew install cloudflared"
    echo "  Linux: sudo apt install cloudflared"
    echo ""
    echo "Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    echo ""
    exit 1
fi

# Check if Flask is available
python3 -c "import flask" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install flask gspread google-auth selenium
}

echo "Starting Flask server in background..."
./start_server.sh &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

echo ""
echo "Starting Cloudflare Tunnel..."
echo ""
echo "============================================================"
echo "IMPORTANT: Copy the URL below (https://xxxxx.trycloudflare.com)"
echo "and paste it into your Google Apps Script SCRAPER_URL"
echo "============================================================"
echo ""

# Start cloudflared tunnel (this will block and show the tunnel info)
cloudflared tunnel --url http://localhost:$PORT

# When cloudflared is stopped (Ctrl+C), also stop Flask
echo ""
echo "Stopping Flask server..."
kill $FLASK_PID 2>/dev/null
echo "All services stopped."
