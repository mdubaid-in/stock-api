@echo off
REM Installation script for Twelve Data Stock Market Application (Windows)

echo ============================================================
echo Twelve Data Stock Market Application - Installation
echo ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

echo [2/4] Creating virtual environment...
python -m venv .venv
.venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created successfully
echo.


echo [3/4] Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Setting up configuration...

REM Check if .env exists
if not exist .env (
    echo Creating .env file...
    echo # Twelve Data API Key (REQUIRED) > .env
    echo # Get your free API key from: https://twelvedata.com/apikey >> .env
    echo TWELVEDATA_API_KEY=your_api_key_here >> .env
    echo. >> .env
    echo # MongoDB Configuration (OPTIONAL) >> .env
    echo MONGO_JOB_SERVER_URI=mongodb://localhost:27017/ >> .env
    echo MONGO_DB_NAME=stock_market >> .env
    
    echo.
    echo ============================================================
    echo Installation Complete!
    echo ============================================================
    echo.
    echo NEXT STEPS:
    echo.
    echo 1. Get your FREE API key:
    echo    Visit: https://twelvedata.com/apikey
    echo    Sign up ^(no credit card required^)
    echo    Copy your API key
    echo.
    echo 2. Edit .env file and replace 'your_api_key_here' with your actual API key
    echo.
    echo 3. Run the application:
    echo    python main.py
    echo.
    echo For detailed instructions, see SETUP_GUIDE.md
    echo ============================================================
) else (
    echo .env file already exists, skipping...
    echo.
    echo ============================================================
    echo Installation Complete!
    echo ============================================================
    echo.
    echo To run the application: python main.py
    echo For detailed instructions, see SETUP_GUIDE.md
    echo ============================================================
)

pause

