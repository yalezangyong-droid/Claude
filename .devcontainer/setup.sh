#!/bin/bash
# Setup script for GitHub Codespaces

set -e

echo "=============================================="
echo "Setting up LinkedIn Scraper in Codespaces"
echo "=============================================="

# Install Chrome
echo "Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=============================================="
echo "Setup complete!"
echo "=============================================="
echo ""
echo "To run the scraper:"
echo "  1. Open the Desktop (port 6080) from the Ports tab"
echo "  2. Run: python linkedin_scraper.py --days 30"
echo "  3. Login to LinkedIn in the browser window"
echo ""
