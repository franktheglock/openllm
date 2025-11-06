@echo off
echo ========================================
echo Discord LLM Bot - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Make sure Python 3.10+ is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo.
echo Checking dependencies...
python -c "import discord" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Edit .env file with your:
    echo - Discord Bot Token
    echo - LLM API Keys
    echo ========================================
    echo.
    echo Opening .env file...
    notepad .env
    echo.
    echo After editing .env, press any key to continue...
    pause >nul
)

REM Run setup wizard if not configured
echo.
echo Checking configuration...
python -c "from src.config.manager import ConfigManager; cm = ConfigManager(); exit(0 if cm.is_configured() else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo Running setup wizard...
    python main.py --setup
    if errorlevel 1 (
        echo Error: Setup failed
        pause
        exit /b 1
    )
)

REM Start the bot in a new window (activate venv there) and open the dashboard in a browser
echo.
echo ========================================
echo Starting Discord LLM Bot in a new window...
echo ========================================
echo.
REM Launch a new cmd window, activate the virtual env there, and run the bot so the current
REM window remains for logs and doesn't need to keep the venv active.
start "" /min cmd /k "call venv\Scripts\activate && python main.py"

REM Give the server a moment to start, then ask whether to open the dashboard in the default browser.
echo Waiting for dashboard to become available...
timeout /t 3 /nobreak >nul

echo.
echo Press ENTER to open the dashboard in your default browser.
echo If you don't want to open it, press Ctrl+C to cancel or type N then press ENTER to skip.
set /p OPEN_BROWSER=Press ENTER to open dashboard (or type N then ENTER to skip): 
if /I "%OPEN_BROWSER%"=="" (
    start "" "http://127.0.0.1:5000"
    echo Launched dashboard in your default browser. The bot is running in the new window.
) else (
    echo Skipping opening the browser. The bot is running in the new window.
)
