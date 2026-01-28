#!/bin/bash
# ============================================================
# LinkedIn Scraper Server - Mac/Linux Startup Script
# ============================================================

# Set your configuration here
GOOGLE_SHEET_ID="1Gv36EQuIC2E04E8dResLMa_K9xU6i1rc4Bubsi3FS1M"
GOOGLE_SHEET_NAME="Will's LinkedIn Automated Tracker"
GOOGLE_CREDENTIALS="credentials.json"
PORT=5000

echo "============================================================"
echo "LinkedIn Scraper Server"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  Sheet ID: $GOOGLE_SHEET_ID"
echo "  Sheet Name: $GOOGLE_SHEET_NAME"
echo "  Credentials: $GOOGLE_CREDENTIALS"
echo ""
echo "Server will start on http://localhost:$PORT"
echo ""
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3."
    exit 1
fi

# Check if required packages are installed
python3 -c "import flask" 2>/dev/null || {
    echo "Installing Flask..."
    pip3 install flask
}

python3 -c "import gspread" 2>/dev/null || {
    echo "Installing gspread and google-auth..."
    pip3 install gspread google-auth
}

python3 -c "import selenium" 2>/dev/null || {
    echo "Installing selenium..."
    pip3 install selenium
}

echo ""
echo "Starting Flask server..."
echo "Press Ctrl+C to stop"
echo ""

python3 scraper_server.py \
    --port $PORT \
    --sheet-id "$GOOGLE_SHEET_ID" \
    --sheet-name "$GOOGLE_SHEET_NAME" \
    --credentials "$GOOGLE_CREDENTIALS"
