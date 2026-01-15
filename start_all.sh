#!/bin/bash
# ============================================================
# LinkedIn Scraper - Start Both Server and ngrok (Mac/Linux)
# ============================================================
# This script starts both Flask server and ngrok in one command
# ============================================================

PORT=5000

echo "============================================================"
echo "LinkedIn Scraper - Full Stack Startup"
echo "============================================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ERROR: ngrok not found!"
    echo ""
    echo "Please install ngrok first:"
    echo "  brew install ngrok   (if you have Homebrew)"
    echo "  OR download from https://ngrok.com/download"
    echo ""
    echo "After installing, configure your authtoken:"
    echo "  ngrok config add-authtoken YOUR_TOKEN"
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
echo "Starting ngrok tunnel..."
echo ""
echo "============================================================"
echo "IMPORTANT: Copy the 'Forwarding' URL (https://xxxxx.ngrok.io)"
echo "and paste it into your Google Apps Script SCRAPER_URL"
echo "============================================================"
echo ""

# Start ngrok (this will block and show the tunnel info)
ngrok http $PORT

# When ngrok is stopped (Ctrl+C), also stop Flask
echo ""
echo "Stopping Flask server..."
kill $FLASK_PID 2>/dev/null
echo "All services stopped."
