#!/bin/bash

echo "========================================"
echo "Discord LLM Bot - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        echo "Make sure Python 3.10+ is installed"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

# Check if dependencies are installed
echo ""
echo "Checking dependencies..."
python -c "import discord" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "========================================"
    echo "IMPORTANT: Edit .env file with your:"
    echo "- Discord Bot Token"
    echo "- LLM API Keys"
    echo "========================================"
    echo ""
    echo "Opening .env file in editor..."
    ${EDITOR:-nano} .env
fi

# Run setup wizard if not configured
echo ""
echo "Checking configuration..."
python -c "from src.config.manager import ConfigManager; cm = ConfigManager(); exit(0 if cm.is_configured() else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Running setup wizard..."
    python main.py --setup
    if [ $? -ne 0 ]; then
        echo "Error: Setup failed"
        exit 1
    fi
fi

# Start the bot
echo ""
echo "========================================"
echo "Starting Discord LLM Bot..."
echo "========================================"
echo ""
python main.py

# If bot exits with error, pause
if [ $? -ne 0 ]; then
    echo ""
    echo "Bot exited with error"
    read -p "Press Enter to continue..."
fi
