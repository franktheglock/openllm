# Setup Guide

This guide will walk you through setting up the Discord LLM Bot from scratch.

## Prerequisites

- **Python 3.10 or higher**
- **Discord Bot Token** ([Create one here](https://discord.com/developers/applications))
- **API keys** for at least one LLM provider:
  - OpenAI API key, OR
  - Anthropic API key, OR
  - OpenRouter API key, OR
  - Local Ollama installation

## Step 1: Install Python

### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```

### macOS/Linux

Python is usually pre-installed. If not:

```bash
# macOS (using Homebrew)
brew install python3

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Verify
python3 --version
```

## Step 2: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name and click "Create"
4. Go to the "Bot" tab
5. Click "Add Bot"
6. Under "Token", click "Reset Token" and copy it (you'll need this later)
7. Enable these Privileged Gateway Intents:
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT
8. Go to OAuth2 > URL Generator
9. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
10. Select bot permissions:
    - ✅ Read Messages/View Channels
    - ✅ Send Messages
    - ✅ Read Message History
11. Copy the generated URL and open it in your browser to invite the bot to your server

## Step 3: Get LLM API Keys

Choose at least one provider:

### OpenAI (Recommended for beginners)

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy and save it securely

### Anthropic (Claude)

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Go to API Keys
4. Create a new key
5. Copy and save it

### OpenRouter (Multiple providers)

1. Go to [openrouter.ai](https://openrouter.ai/)
2. Sign up with GitHub or email
3. Go to Keys section
4. Create a new API key
5. Copy and save it

### Ollama (Local, Free)

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Run: `ollama pull llama2`
3. Start Ollama: `ollama serve`
4. No API key needed!

## Step 4: Clone/Download the Bot

```bash
# Clone the repository (if using git)
git clone <repository-url>
cd discord-llm-bot

# OR download and extract the ZIP file, then navigate to the folder
cd path/to/discord-llm-bot
```

## Step 5: Create Virtual Environment

This keeps the bot's dependencies isolated:

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

## Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all necessary packages. It may take a few minutes.

## Step 7: Configure Environment

1. Copy the example environment file:
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS/Linux
   cp .env.example .env
   ```

2. Edit `.env` with your favorite text editor and add your tokens:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   OPENAI_API_KEY=your_openai_key_here
   # Add other API keys as needed
   ```

## Step 8: Run Setup Wizard

The setup wizard will guide you through configuration:

```bash
python main.py --setup
```

You'll be asked to:
1. Enter your Discord bot token
2. Choose an LLM provider
3. Enter API key(s)
4. Configure tools (web search, etc.)
5. Set optional features

## Step 9: Start the Bot

```bash
python main.py
```

You should see:
```
[INFO] Discord LLM Bot initialized
[INFO] Bot logged in as YourBotName#1234
```

## Step 10: Test the Bot

In your Discord server, try:

```
@YourBot hello!
```

The bot should respond using the configured LLM!

## Step 11: Access the Dashboard (Optional)

Open your web browser and go to:
```
http://localhost:5000
```

You'll see the dashboard where you can:
- View connected servers
- Monitor usage and costs
- Configure settings
- Manage plugins

## Common Issues

### "DISCORD_TOKEN not found"

- Make sure you created the `.env` file
- Check that the token is correctly pasted
- No quotes around the token in `.env`

### "Module not found"

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### "Bot is online but not responding"

- Check that MESSAGE CONTENT INTENT is enabled in Discord Developer Portal
- Try mentioning the bot: `@YourBot hello`
- Check the logs for errors

### "OpenAI API error: 401"

- API key is invalid or expired
- Check your API key in `.env`
- Ensure you have credits in your OpenAI account

## Advanced Configuration

### Custom System Prompt

Edit `config.yaml`:

```yaml
prompts:
  system: |
    You are a helpful assistant specialized in [your domain].
    Be concise and friendly.
```

### Per-Server Configuration

Use the dashboard or edit server configs via the API to customize settings for each Discord server.

### Adding Web Search

During setup, enable web search and choose a provider:
- **DuckDuckGo**: Free, no API key needed (recommended)
- **Google**: Requires API key and Custom Search Engine ID
- **Brave**: Requires API key
- **SearxNG**: Requires self-hosted instance

### Temperature and Creativity

In `config.yaml`:

```yaml
llm:
  temperature: 0.7  # 0.0 = focused, 2.0 = creative
  max_tokens: 2048  # Maximum response length
```

## Updating the Bot

```bash
# Pull latest changes (if using git)
git pull

# Activate virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart the bot
python main.py
```

## Running as a Service (Production)

### Windows (Task Scheduler)

1. Create a batch file `start_bot.bat`:
   ```batch
   @echo off
   cd C:\path\to\discord-llm-bot
   call venv\Scripts\activate
   python main.py
   ```

2. Open Task Scheduler
3. Create Basic Task
4. Set trigger (e.g., "At startup")
5. Set action to run `start_bot.bat`

### Linux (systemd)

1. Create service file `/etc/systemd/system/discord-bot.service`:
   ```ini
   [Unit]
   Description=Discord LLM Bot
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/discord-llm-bot
   ExecStart=/path/to/discord-llm-bot/venv/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start:
   ```bash
   sudo systemctl enable discord-bot
   sudo systemctl start discord-bot
   sudo systemctl status discord-bot
   ```

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Rotate API keys** regularly
3. **Use environment variables** for sensitive data
4. **Enable moderation** if bot is in public servers
5. **Monitor usage** via dashboard to prevent abuse

## Getting Help

- Check the [README.md](../README.md) for general information
- Read [Plugin Development Guide](PLUGIN_DEVELOPMENT.md) for extending functionality
- Check logs in `logs/bot.log` for errors
- Review `config.yaml` for all available options

## Next Steps

- Explore the dashboard at `http://localhost:5000`
- Try different LLM providers and models
- Install plugins from the community
- Create your own custom tools
- Configure per-server settings

Enjoy your Discord LLM Bot! 🤖✨
