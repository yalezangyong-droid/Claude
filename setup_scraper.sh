#!/bin/bash
#
# Setup script for LinkedIn Post Scraper
# Installs Python dependencies and ChromeDriver
#

set -e

echo "=============================================="
echo "LinkedIn Post Scraper Setup"
echo "=============================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check Chrome installation
echo ""
echo "Checking Chrome installation..."
if command -v google-chrome &> /dev/null; then
    echo "Chrome found: $(google-chrome --version)"
elif command -v google-chrome-stable &> /dev/null; then
    echo "Chrome found: $(google-chrome-stable --version)"
elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "Chrome found (macOS)"
else
    echo ""
    echo "WARNING: Chrome not found. Please install Google Chrome:"
    echo "  - Linux: sudo apt install google-chrome-stable"
    echo "  - macOS: Download from https://www.google.com/chrome/"
    echo ""
fi

# ChromeDriver is handled automatically by selenium-manager (Selenium 4.6+)
echo ""
echo "Note: ChromeDriver will be automatically managed by Selenium."

echo ""
echo "=============================================="
echo "Setup complete!"
echo "=============================================="
echo ""
echo "To run the scraper:"
echo "  source venv/bin/activate"
echo "  python linkedin_scraper.py --days 30"
echo ""
echo "First run will open Chrome for manual LinkedIn login."
echo "Your session will be saved for future runs."
echo ""
