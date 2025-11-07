@echo off
echo Setting up OpenLLM environment...

REM Check if virtual environment exists and is valid
if exist venv\Scripts\activate.bat (
    echo Virtual environment already exists.
) else (
    echo Creating virtual environment...
    if exist venv (
        echo Removing incomplete virtual environment...
        rmdir /s /q venv
    )
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Make sure Python is installed.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    echo Please ensure the virtual environment was created correctly.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

REM Install requirements
if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
) else (
    echo requirements.txt not found. Please ensure it exists.
    pause
    exit /b 1
)

REM Launch web setup wizard
echo Launching web setup wizard...
python main.py --setup
if errorlevel 1 (
    echo Setup wizard failed to launch.
    pause
    exit /b 1
)

echo Setup complete!
pause