#!/bin/bash
# Installation script for Twelve Data Stock Market Application (Linux/Mac)

echo "============================================================"
echo "Twelve Data Stock Market Application - Installation"
echo "============================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "[1/3] Checking Python version..."
python3 --version

echo ""
echo "[2/3] Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "[3/3] Setting up configuration..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Twelve Data API Key (REQUIRED)
# Get your free API key from: https://twelvedata.com/apikey
TWELVEDATA_API_KEY=your_api_key_here

# MongoDB Configuration (OPTIONAL)
MONGO_JOB_SERVER_URI=mongodb://localhost:27017/
MONGO_DB_NAME=stock_market
EOF
    
    echo ""
    echo "============================================================"
    echo "Installation Complete!"
    echo "============================================================"
    echo ""
    echo "NEXT STEPS:"
    echo ""
    echo "1. Get your FREE API key:"
    echo "   Visit: https://twelvedata.com/apikey"
    echo "   Sign up (no credit card required)"
    echo "   Copy your API key"
    echo ""
    echo "2. Edit .env file and replace 'your_api_key_here' with your actual API key"
    echo ""
    echo "3. Run the application:"
    echo "   python3 main.py"
    echo ""
    echo "For detailed instructions, see SETUP_GUIDE.md"
    echo "============================================================"
else
    echo ".env file already exists, skipping..."
    echo ""
    echo "============================================================"
    echo "Installation Complete!"
    echo "============================================================"
    echo ""
    echo "To run the application: python3 main.py"
    echo "For detailed instructions, see SETUP_GUIDE.md"
    echo "============================================================"
fi

# Make script executable
chmod +x install.sh

