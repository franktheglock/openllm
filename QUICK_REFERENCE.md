# Discord LLM Bot - Quick Reference

## Common Commands

### Starting the Bot

```bash
# Quick start (Windows)
start.bat

# Quick start (Linux/Mac)
./start.sh

# Manual start
python main.py

# Run setup wizard
python main.py --setup

# Start without dashboard
python main.py --no-dashboard
```

### Using the Bot in Discord

```
# Mention the bot
@BotName what is Python?

# Use prefix
!tell me a joke

# The bot will automatically use tools when needed
@BotName what's the weather in Tokyo?
```

## File Locations

| File/Directory | Purpose |
|----------------|---------|
| `main.py` | Entry point |
| `config.yaml` | Main configuration |
| `.env` | API keys and secrets |
| `src/bot.py` | Core bot logic |
| `src/llm/` | LLM provider implementations |
| `src/tools/` | Bot tools (web search, etc.) |
| `src/plugins/` | Plugin system |
| `dashboard/` | Web dashboard |
| `plugins/` | Installed plugins |
| `data/bot.db` | SQLite database |
| `logs/bot.log` | Log file |

## Configuration Quick Reference

### LLM Providers

```yaml
llm:
  default_provider: "openai"  # or "anthropic", "ollama", "openrouter"
  default_model: "gpt-4-turbo-preview"
  temperature: 0.7  # 0.0 = focused, 2.0 = creative
  max_tokens: 2048
```

### Enable/Disable Features

```yaml
tools:
  web_search:
    enabled: true  # or false

plugins:
  enabled: true  # or false

dashboard:
  enabled: true  # or false
  port: 5000

moderation:
  enabled: false  # or true
```

## Environment Variables (.env)

```env
# Required
DISCORD_TOKEN=your_token_here

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...

# Web Search (optional)
GOOGLE_API_KEY=...
GOOGLE_CSE_ID=...
BRAVE_API_KEY=...
SEARXNG_URL=http://localhost:8080
```

## Dashboard URLs

| Page | URL |
|------|-----|
| Main Dashboard | http://localhost:5000 |
| Bot Status | http://localhost:5000/api/status |
| Configuration | http://localhost:5000/api/config |
| Servers | http://localhost:5000/api/servers |
| Usage Stats | http://localhost:5000/api/usage/stats |
| Tools | http://localhost:5000/api/tools |
| Providers | http://localhost:5000/api/providers |

## Database Queries

```sql
-- View usage statistics
SELECT * FROM usage_stats ORDER BY timestamp DESC LIMIT 10;

-- Get total cost
SELECT SUM(cost_usd) as total_cost FROM usage_stats;

-- Server configurations
SELECT * FROM server_config;

-- Installed plugins
SELECT * FROM plugins;
```

## Common Issues & Solutions

### Bot won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Verify dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env  # or dir .env on Windows
```

### Import errors
```bash
# Ensure virtual environment is activated
# You should see (venv) in your terminal

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Bot doesn't respond
1. Check MESSAGE CONTENT INTENT is enabled
2. Verify bot has permissions in the channel
3. Try mentioning the bot directly: `@BotName`
4. Check logs: `tail -f logs/bot.log`

### API errors
1. Verify API key is correct in `.env`
2. Check you have credits/quota
3. Try a different model
4. Review error in `logs/bot.log`

## Useful Python Commands

```python
# Check configuration
python -c "from src.config.manager import ConfigManager; cm = ConfigManager(); print(cm.config)"

# Test LLM provider
python -c "from src.llm.factory import LLMProviderFactory; print(LLMProviderFactory.get_available_providers())"

# Check database
python -c "import sqlite3; conn = sqlite3.connect('data/bot.db'); print(conn.execute('SELECT COUNT(*) FROM usage_stats').fetchone())"
```

## Log Files

```bash
# View logs (Linux/Mac)
tail -f logs/bot.log

# View logs (Windows)
type logs\bot.log

# Search for errors
grep ERROR logs/bot.log  # Linux/Mac
findstr ERROR logs\bot.log  # Windows
```

## Updating Configuration

```bash
# Edit config file
nano config.yaml  # Linux/Mac
notepad config.yaml  # Windows

# Restart bot to apply changes
# (or use dashboard for runtime changes)
```

## Plugin Management

```bash
# List plugins
ls plugins/  # Linux/Mac
dir plugins\  # Windows

# Install plugin
# 1. Create directory: plugins/plugin_name/
# 2. Add manifest.json and plugin.py
# 3. Restart bot or use dashboard

# Enable/disable via database
sqlite3 data/bot.db "UPDATE plugins SET enabled=1 WHERE name='plugin_name'"
```

## Cost Monitoring

```python
# Quick cost check
python -c "
import sqlite3
conn = sqlite3.connect('data/bot.db')
result = conn.execute('SELECT SUM(cost_usd) FROM usage_stats').fetchone()
print(f'Total cost: ${result[0]:.4f}')
"
```

## Backup & Restore

```bash
# Backup database
cp data/bot.db data/bot.db.backup  # Linux/Mac
copy data\bot.db data\bot.db.backup  # Windows

# Backup configuration
cp config.yaml config.yaml.backup
cp .env .env.backup

# Restore
cp data/bot.db.backup data/bot.db
```

## Performance Tips

1. **Use cheaper models for development**:
   ```yaml
   default_model: "gpt-3.5-turbo"  # instead of gpt-4
   ```

2. **Limit token usage**:
   ```yaml
   max_tokens: 500  # instead of 2048
   ```

3. **Enable caching**:
   ```yaml
   performance:
     cache_enabled: true
     cache_ttl_seconds: 3600
   ```

4. **Use local models** (free):
   ```bash
   ollama pull llama2
   # Set provider to "ollama" in config
   ```

## Model Recommendations

| Use Case | Provider | Model |
|----------|----------|-------|
| General Chat | OpenAI | gpt-4-turbo-preview |
| Cost-Effective | OpenAI | gpt-3.5-turbo |
| Creative Writing | Anthropic | claude-3-opus |
| Fast Responses | Anthropic | claude-3-haiku |
| Local/Free | Ollama | llama2 |
| Coding Help | OpenAI | gpt-4 |

## Temperature Guide

| Value | Use For |
|-------|---------|
| 0.0-0.2 | Math, code, facts |
| 0.3-0.5 | Technical writing |
| 0.6-0.8 | General conversation |
| 0.9-1.1 | Creative writing |
| 1.2-2.0 | Experimental/artistic |

## Support Resources

- **Setup Guide**: `docs/SETUP.md`
- **Plugin Guide**: `docs/PLUGIN_DEVELOPMENT.md`
- **Examples**: `docs/EXAMPLES.md`
- **Project Overview**: `PROJECT_OVERVIEW.md`
- **Checklist**: `CHECKLIST.md`
- **Logs**: `logs/bot.log`

---

Keep this file handy for quick reference! 📋
