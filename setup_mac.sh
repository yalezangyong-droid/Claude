#!/bin/bash
# LinkedIn Tracker - Mac Setup Script

echo "🚀 LinkedIn Tracker Setup for Mac"
echo "=================================="
echo ""

# Check Python
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Check pip
echo "✓ Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed"
    exit 1
fi

PIP_VERSION=$(pip3 --version)
echo "✓ Found: $PIP_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "⬇️  Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Verify installation
echo "🧪 Testing installation..."
if python linkedin_tracker.py --help > /dev/null 2>&1; then
    echo "✅ Installation successful!"
    echo ""
    echo "🎉 You're all set! Here's what to do next:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Set up LinkedIn authentication:"
    echo "   python linkedin_auth_setup.py"
    echo ""
    echo "3. Start tracking:"
    echo "   python linkedin_auto_tracker.py --monitor"
    echo ""
else
    echo "❌ Installation test failed"
    echo "Please check the error messages above"
fi
