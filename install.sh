#!/bin/bash

# Timetable Generator Installation Script

echo "Timetable Generator - Installation Script"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✓ pip3 found: $(pip3 --version)"

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Test installation
echo ""
echo "Testing installation..."
python3 test_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "To run the application:"
    echo "  python3 main.py"
    echo ""
    echo "To test example usage:"
    echo "  python3 example_usage.py"
    echo ""
    echo "To test installation again:"
    echo "  python3 test_installation.py"
else
    echo ""
    echo "⚠ Installation completed but some tests failed."
    echo "Please check the error messages above."
fi
