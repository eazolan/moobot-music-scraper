#!/bin/bash
# Moobot Scraper Installation Script for Linux

set -e  # Exit on any error

echo "Installing Moobot Scraper Dependencies..."
echo "=========================================="
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if command_exists python3; then
    PYTHON_CMD="python3"
    echo "✓ Found Python: $(python3 --version)"
elif command_exists python; then
    # Check if it's Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
        echo "✓ Found Python: $(python --version)"
    else
        echo "ERROR: Python 3 is required, but found: $(python --version)"
        echo "Please install Python 3.7+ from your package manager"
        exit 1
    fi
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.7+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    exit 1
fi

# Check for pip
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo "ERROR: pip is not available"
    echo "Please install pip using your package manager"
    exit 1
fi

echo
echo "Installing required packages..."
echo "==============================="

# Install requirements
if $PYTHON_CMD -m pip install -r requirements.txt; then
    echo
    echo "==============================================="
    echo "Installation complete!"
    echo "==============================================="
    echo
    echo "To test the scraper, run:"
    echo "  $PYTHON_CMD test_scraper.py"
    echo
    echo "To start continuous monitoring, run:"
    echo "  $PYTHON_CMD moobot_scraper.py"
    echo
else
    echo
    echo "ERROR: Failed to install packages"
    echo "Try one of the following:"
    echo "  - Run with sudo if installing globally"
    echo "  - Use a virtual environment"
    echo "  - Check your internet connection"
    exit 1
fi