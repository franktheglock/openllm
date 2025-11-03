# Development Guide

This guide covers development workflows, testing, and debugging for the Discord LLM Bot.

## 🚀 Getting Started

### Setting Up Development Environment

1. **Clone and setup virtual environment**
   ```bash
   git clone <repository>
   cd discord-llm-bot
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run initial setup**
   ```bash
   python main.py --setup
   ```

## 🧪 Testing & Development Commands

### Reset Configuration
During development, you'll often need to test the setup process. Use the reset command:

```bash
python main.py --reset
```

**What it does:**
- Deletes `.env` file
- Deletes `config.yaml`
- Removes `data/` directory (database)
- Clears Python `__pycache__`
- Automatically launches setup wizard

**Use cases:**
- Testing the setup wizard
- Switching between different LLM providers
- Clean slate after major config changes
- Reproducing first-run user experience

### Other Flags

```bash
# Run setup wizard without resetting
python main.py --setup

# Start bot without web dashboard
python main.py --no-dashboard

# Specify custom config file
python main.py --config my_config.yaml
```

## 🔧 Project Structure

```
discord-llm-bot/
├── main.py                 # Entry point
├── src/
│   ├── bot.py             # Core bot logic
│   ├── llm/               # LLM provider implementations
│   │   ├── factory.py     # Provider factory
│   │   ├── base.py        # Base provider class
│   │   ├── gemini_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── ollama_provider.py
│   │   └── openrouter_provider.py
│   ├── config/            # Configuration management
│   │   └── manager.py
│   ├── tools/             # Bot tools (web search, etc.)
│   ├── plugins/           # Plugin system
│   ├── utils/             # Utilities
│   └── setup_wizard_gui.py  # GUI setup wizard
├── dashboard/             # Web dashboard
│   ├── app.py            # Flask application
│   └── templates/        # HTML templates
├── plugins/              # User plugins directory
├── data/                 # Database (auto-created)
├── config.yaml          # Main config (auto-created)
└── .env                 # Environment variables (auto-created)
```

## 🧩 Adding a New LLM Provider

1. **Create provider class** in `src/llm/`
   ```python
   from src.llm.base import BaseLLMProvider
   
   class MyProvider(BaseLLMProvider):
       def __init__(self):
           api_key = os.getenv('MY_PROVIDER_API_KEY')
           # Initialize your provider
       
       async def complete(self, messages, **kwargs):
           # Implement completion logic
           pass
       
       def get_available_models(self):
           return ['model-1', 'model-2']
       
       def estimate_cost(self, tokens_in, tokens_out, model):
           # Calculate cost
           return cost
   ```

2. **Register in factory** (`src/llm/factory.py`)
   ```python
   from src.llm.my_provider import MyProvider
   
   _providers = {
       'my_provider': MyProvider,
       # ... other providers
   }
   ```

3. **Add to setup wizard** (`src/setup_wizard_gui.py`)
   - Add to provider list in `show_llm_step()`
   - Add API key field
   - Update `.env.example`

4. **Update dashboard** (`dashboard/app.py`)
   - Add to `provider_info` dict in `api_providers()`

## 🔌 Creating Plugins

See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for detailed plugin development guide.

Quick example:

```python
# plugins/my_plugin/plugin.py
class MyPlugin:
    def __init__(self, bot):
        self.bot = bot
    
    async def on_message(self, message):
        # Handle messages
        pass
    
    async def my_tool(self, **kwargs):
        # Tool function
        return "Result"
```

```json
// plugins/my_plugin/manifest.json
{
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Does something cool",
  "permissions": ["network"],
  "tools": [
    {
      "name": "my_tool",
      "description": "My custom tool",
      "parameters": {}
    }
  ]
}
```

## 🐛 Debugging

### Enable Debug Logging

Edit `src/utils/logger.py` or set log level in code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Setup wizard won't start:**
- Check if tkinter/customtkinter is installed
- Try: `pip install customtkinter`

**Bot won't connect:**
- Verify Discord token in `.env`
- Check bot permissions in Discord Developer Portal
- Ensure MESSAGE CONTENT INTENT is enabled

**LLM provider errors:**
- Verify API key is correct
- Check API key has sufficient credits
- Review provider-specific rate limits

**Database errors:**
- Delete `data/` directory and restart
- Or use `python main.py --reset`

## 📊 Testing

### Manual Testing

```bash
# Test setup wizard
python main.py --reset

# Test specific provider
# Edit .env to set DEFAULT_LLM_PROVIDER=gemini
python main.py
```

### Unit Tests (if implemented)

```bash
pytest tests/
```

## 🚀 Dashboard Development

The dashboard is built with Flask and vanilla JavaScript.

**Development server:**
```python
# dashboard/app.py runs on http://localhost:5000
# Auto-reloads when Flask debug mode enabled
```

**Making dashboard changes:**
1. Edit `dashboard/templates/index.html` for frontend
2. Edit `dashboard/app.py` for backend API
3. Refresh browser to see changes

**API Endpoints:**
- `GET /api/status` - Bot status
- `GET /api/config` - Current configuration
- `POST /api/config/llm` - Update LLM settings
- `POST /api/tools/toggle` - Enable/disable tools
- `GET /api/providers` - Available providers
- `GET /api/servers` - Connected servers
- `GET /api/usage/stats` - Usage statistics

## 🎨 Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Keep functions focused and small

```python
def my_function(param: str) -> Dict[str, Any]:
    """
    Brief description.
    
    Args:
        param: Description
        
    Returns:
        Description of return value
    """
    pass
```

## 🔄 Workflow Tips

1. **Use --reset frequently** when testing setup changes
2. **Check logs** in console for errors
3. **Test with multiple providers** to ensure compatibility
4. **Use dashboard** for quick config changes during development
5. **Keep .env.example updated** when adding new environment variables

## 📝 Contributing

When contributing:

1. Create feature branch
2. Make changes
3. Test with `--reset` to verify setup works
4. Update documentation
5. Submit pull request

## 🆘 Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [API Documentation](API.md)
- See [Examples](EXAMPLES.md)
