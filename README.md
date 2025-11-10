an entirely vibecoded discord bot platform!
im planning on keeping this updated and adding new features
at the moment there is no plugin marketplace but its very early days
all contributions welcome and appreciated (especially gui imrovements lol)











# 🤖 OpenLLM

OpenLLM — a powerful Discord assistant platform powered by Large Language Models with a modern web dashboard and extensive customization options.

## ✨ Features

- 🧠 **Multi-LLM Support**: Google Gemini (recommended), OpenAI, Anthropic, OpenRouter, Ollama, LM Studio, Custom OpenAI-compatible endpoints
- 🎨 **Modern Web Dashboard**: Dark-mode, mobile-friendly web interface for configuration and monitoring
- 🔑 **Provider Management**: Configure API keys and endpoints directly from the dashboard
- 🌐 **Web Setup Wizard**: Browser-based setup experience with guided configuration
- 🔧 **Highly Customizable**: Plugin system and MCP server integration
- 🔍 **Web Search**: Built-in web search tool with multiple providers
- 🛡️ **Content Moderation**: Optional message policy screening
- 📊 **Analytics**: Usage statistics and cost tracking
- 🔌 **Plugin Marketplace**: Browse and install community extensions
- 🪟 **Windows Support**: One-click setup with `setup.bat`
- 📱 **Mobile Friendly**: Access dashboard from your phone with responsive design
 - 🐧 **Unix Quick Start**: `start.sh` (Linux) and `start_macos.sh` (macOS) available for one-step setup/start

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- API keys for your chosen LLM provider(s)

### Installation

#### Windows Installer (Easiest)

**New! Download the all-in-one Windows installer (no Python required):**

1. Download `OpenLLM-Setup-Standalone.exe` from releases (run as administrator) 
2. Run the installer (includes Python 3.11.9 - no prerequisites!)
3. Launch OpenLLM from Start Menu or Desktop

**Alternative:** If you already have Python installed, download `OpenLLM-Setup.exe` instead (smaller download)

The installer includes everything you need to run OpenLLM - no separate Python installation required for the standalone version!

**To build the installer yourself**, see [BUILD_INSTALLER.md](BUILD_INSTALLER.md).

#### Windows (Script-based)

1. **Download/Clone the repository**
   ```bash
   git clone <repository-url>
   cd openllm
   ```

2. **Run the setup script**
   ```bash
   # Double-click setup.bat or run from command prompt
   setup.bat
   ```
   
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Launch the web setup wizard in your browser

#### Linux/Mac

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd openllm
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows (alternative)
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation** (optional)
   ```bash
   python check_install.py
   ```

5. **Run web setup wizard**
   ```bash
   python main.py --setup
   ```
   
   The setup wizard will open in your browser and guide you through:
   - Discord bot configuration
   - LLM provider selection (Gemini recommended for best value)
   - Tool configuration
   - API key setup

6. **Start the bot**
   ```bash
   python main.py
   ```

Alternatively, the repo includes quick-start scripts to automate these steps:

- Linux (all-in-one):
   ```bash
   chmod +x ./start.sh
   ./start.sh
   ```

- macOS (Terminal.app):
   ```bash
   chmod +x ./start_macos.sh
   ./start_macos.sh
   ```

These scripts will create/activate the virtual environment, install dependencies if needed, run the setup wizard (if configuration is missing), start the bot in a new terminal window, and open the dashboard in your browser.

#### Docker (Easy Setup)

For the easiest deployment, use Docker:

1. **Quick start with docker-compose** (recommended)
   
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd openllm

   # Start the container
   docker-compose up -d
   ```

2. **Complete web-based setup**
   
   On first run, the container will start the web setup wizard:
   - Open `http://localhost:5050/setup` in your browser
   - Or from another device: `http://<your-server-ip>:5050/setup`
   - Follow the guided setup to configure:
     - Discord bot token
     - LLM provider and API keys
     - Optional tools and features
   
   After setup completes, the bot starts automatically!

3. **Access the dashboard**
   - Dashboard: `http://localhost:5000`
   - Or from network: `http://<your-server-ip>:5000`

**Docker Features:**
- ✅ **Web Setup Wizard**: Browser-based configuration on first run
- ✅ **Network Accessible**: Setup from any device on your network
- ✅ **Persistent data**: Configuration and database saved in `./data` volume
- ✅ **Health checks**: Built-in container health monitoring
- ✅ **Easy updates**: Pull new image and restart
- ✅ **Unraid ready**: Compatible with Unraid Community Applications

**Alternative: Manual Docker run**
```bash
docker run -d \
  --name discord-llm-bot \
  -p 5000:5000 \
  -p 5050:5050 \
  -v $(pwd)/data:/app/data \
  your-image-name
```

Then visit `http://localhost:5050/setup` to configure.

**Optional Environment Variables:**
You can still pre-configure using environment variables (they will auto-populate in the setup wizard):
- `BOT_TOKEN` - Your Discord bot token
- `OPENAI_API_KEY` - OpenAI API key
- `GEMINI_API_KEY` - Google Gemini API key
- `ANTHROPIC_API_KEY` - Anthropic/Claude API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `LMSTUDIO_BASE_URL` - LM Studio endpoint
- `CUSTOM_LLM_BASE_URL` - Custom OpenAI-compatible endpoint
- `CUSTOM_LLM_API_KEY` - API key for custom endpoint

**For Unraid users:**
- Map `/mnt/user/appdata/openllm` to `/app/data` for persistence
- Expose ports 5000 (dashboard) and 5050 (setup wizard)
- On first start, access setup wizard at `http://<unraid-ip>:5050/setup`
- After setup, access dashboard at `http://<unraid-ip>:5000`

## 📖 Configuration

### Web Setup Wizard

On first launch or when using `--setup`, a modern web-based wizard will guide you through:

1. Discord bot token configuration
2. Selecting your preferred LLM provider (Gemini recommended)
3. Entering API keys
4. Configuring enabled tools (web search, etc.)
5. Setting up content moderation (optional)

The wizard saves everything to `.env` and `config.yaml` automatically.

### Dashboard Access

Access the web dashboard at: `http://localhost:5000`

From your local network, find the IP address displayed when the bot starts:
```
Dashboard running at http://192.168.1.100:5000
```

From the dashboard you can:
- **Edit Configuration**: Click "Edit Settings" to modify LLM provider, model, temperature, and system prompt
- **AI-Enhanced Prompts**: Use AI to help craft better system prompts
- **Provider Management**: Configure API keys and custom endpoints for all supported providers
- **Local LLM Support**: Configure LM Studio, Ollama, or custom OpenAI-compatible endpoints
- View connected servers and bot status
- Manage plugins and extensions
- View usage statistics and costs
- Monitor real-time activity

### Supported Providers

#### Cloud Providers (Require API Key)
- **Google Gemini** (Recommended) - Best value, high quality
- **OpenAI** - GPT-4, GPT-4o, GPT-3.5
- **Anthropic** - Claude models
- **OpenRouter** - Access to many models through one API

#### Local Providers (No API Key Required)
- **Ollama** - Run models locally (llama2, mistral, etc.)
- **LM Studio** - Local inference server with GUI

#### Custom Endpoints
- **Custom Provider** - Any OpenAI-compatible API endpoint

Configure providers from the **Provider Management** section in the dashboard.

## 🔌 Plugin Development

Create custom plugins to extend the bot's functionality.

### Plugin Structure

```
plugins/
  my_plugin/
    manifest.json
    __init__.py
    plugin.py
```

### Example Manifest

```json
{
  "name": "My Custom Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A custom plugin example",
  "permissions": ["network", "storage"],
  "tools": [
    {
      "name": "my_tool",
      "description": "Does something cool",
      "parameters": {
        "query": "string"
      }
    }
  ]
}
```

See [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) for details.

## 🛠️ Built-in Tools

### Web Search
Searches the web for real-time information using your configured provider.

```python
# Available providers:
- Google Custom Search
- DuckDuckGo
- Brave Search
- SearxNG
```

## 📊 Usage Examples

### Running the Bot

```bash
# Normal start
python main.py

# Run setup wizard
python main.py --setup

# Reset configuration (for testing/development)
python main.py --reset

# Start without dashboard
python main.py --no-dashboard
```

### Basic Chat
```
@BotName what's the weather like today?
```

### With Web Search
```
@BotName search for the latest news about AI
```

### Multi-turn Conversation
The bot maintains context within a conversation thread.

## 🧪 Development & Testing

### Reset Configuration
During development, you can reset all configuration files:

```bash
python main.py --reset
```

This will:
- Delete `.env` file
- Delete `config.yaml`
- Clear database (`data/` directory)
- Clear Python cache
- Launch the setup wizard for fresh configuration

Perfect for testing the setup process or starting fresh!

## 🔐 Security

- API keys stored securely in environment variables
- Plugin sandboxing for safety
- Optional content moderation
- Per-server permission controls

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Discord.py team
- All LLM provider communities
- Contributors and plugin developers
