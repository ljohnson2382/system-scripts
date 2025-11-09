#!/bin/bash
# Quick setup script for Unix/Linux/macOS systems
# Author: Loyd Johnson
# Date: November 2025

set -e  # Exit on any error

echo "=================================================="
echo "  System Scripts Toolkit - Quick Setup (Unix)"
echo "  Author: Loyd Johnson"
echo "=================================================="
echo

# Check Python version
echo "🔍 Checking Python version..."
python3 --version || {
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ and try again"
    exit 1
}

# Create virtual environment
echo "🔄 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "🔄 Installing dependencies..."
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
else
    echo "Installing production dependencies..."
    pip install -r requirements.txt
fi

# Make scripts executable
echo "🔄 Setting script permissions..."
chmod +x auto_update.py
find scripts/ -name "*.py" -exec chmod +x {} \;
chmod +x setup_environment.py

# Test installation
echo "🧪 Testing installation..."
python auto_update.py --check-prereq

echo
echo "🎉 Setup complete!"
echo
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo
echo "To test the tools:"
echo "  python auto_update.py --check-prereq"
echo "  python scripts/helpdesk/system_info.py"
echo "  python scripts/helpdesk/network_diagnostics.py"
echo
echo "To deactivate when done:"
echo "  deactivate"
echo