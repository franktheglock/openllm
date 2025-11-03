an entirely vibecoded discord bot platform!
im planning on keeping this updated and adding new features
at the moment there is no plugin marketplace but its very early days 
all contributions welcome and appreciated (especially gui imrovments lol)











# 🤖 OpenLLM

OpenLLM — a powerful Discord assistant platform powered by Large Language Models with a modern GUI dashboard and extensive customization options.

## ✨ Features

- 🧠 **Multi-LLM Support**: Google Gemini (recommended), OpenAI, Anthropic, OpenRouter, Ollama
- 🎨 **Modern Dashboard**: Fully editable web-based GUI for configuration and monitoring
- 🖥️ **GUI Setup Wizard**: User-friendly setup experience with customtkinter
- 🔧 **Highly Customizable**: Plugin system and MCP server integration
- 🔍 **Web Search**: Built-in web search tool with multiple providers
- 🛡️ **Content Moderation**: Optional message policy screening
- 📊 **Analytics**: Usage statistics and cost tracking
- 🔌 **Plugin Marketplace**: Browse and install community extensions

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- API keys for your chosen LLM provider(s)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd openllm
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation** (optional)
   ```bash
   python check_install.py
   ```

5. **Run GUI Setup Wizard**
   ```bash
   python main.py --setup
   ```
   
   The setup wizard will guide you through:
   - Discord bot configuration
   - LLM provider selection (Gemini recommended for best value)
   - Tool configuration
   - API key setup

6. **Start the bot**
   ```bash
   python main.py
   ```

## 📖 Configuration

### GUI Setup Wizard

On first launch or when using `--setup`, a modern GUI wizard will guide you through:

1. Discord bot token configuration
2. Selecting your preferred LLM provider (Gemini recommended)
3. Entering API keys
4. Configuring enabled tools (web search, etc.)

The wizard saves everything to `.env` and `config.yaml` automatically.

### Dashboard Access

Access the web dashboard at: `http://localhost:5000`

From here you can:
- **Edit Configuration**: Click "Edit Settings" to modify LLM provider, model, temperature, and tools
- View connected servers and bot status
- Manage plugins and extensions
- View usage statistics and costs
- Monitor real-time activity

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
