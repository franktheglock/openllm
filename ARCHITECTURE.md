# Discord LLM Bot - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Discord Platform                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Server 1 │  │ Server 2 │  │ Server 3 │  │   DMs    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
        ┌─────────────────▼───────────────────────────┐
        │         Discord Bot (main.py)               │
        │  ┌────────────────────────────────────┐    │
        │  │    Event Handler & Router          │    │
        │  │  - on_message                       │    │
        │  │  - on_ready                         │    │
        │  │  - Command processing               │    │
        │  └────────┬───────────────────────────┘    │
        └───────────┼──────────────────────────────────┘
                    │
        ┌───────────▼──────────────────────────────────┐
        │         Core Bot Logic (src/bot.py)          │
        │                                               │
        │  ┌─────────────────────────────────────┐    │
        │  │  Conversation Management             │    │
        │  │  - Context per channel/server        │    │
        │  │  - Message history                   │    │
        │  │  - Tool call handling                │    │
        │  └─────────┬───────────────────────────┘    │
        └────────────┼──────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌────▼────┐ ┌───▼─────┐
    │   LLM   │ │  Tools  │ │ Plugins │
    │ Factory │ │ Manager │ │ Manager │
    └────┬────┘ └────┬────┘ └───┬─────┘
         │           │           │
         │           │           │
    ┌────▼──────────────────────────────┐
    │      LLM Provider Layer           │
    │  ┌─────────┐  ┌──────────┐       │
    │  │ OpenAI  │  │Anthropic │       │
    │  └─────────┘  └──────────┘       │
    │  ┌─────────┐  ┌──────────┐       │
    │  │ Ollama  │  │OpenRouter│       │
    │  └─────────┘  └──────────┘       │
    └────┬──────────────────────────────┘
         │
         │ API Calls
         │
    ┌────▼──────────────────────────────┐
    │    External LLM Services          │
    │  - OpenAI API                      │
    │  - Anthropic API                   │
    │  - Local Ollama                    │
    │  - OpenRouter                      │
    └────────────────────────────────────┘
```

## Data Flow

```
User Message (Discord)
    │
    ▼
Discord Bot receives message
    │
    ▼
Check if bot should respond
(mention / prefix / DM)
    │
    ▼
Load server configuration
    │
    ▼
Get/Create conversation context
    │
    ▼
Add user message to context
    │
    ▼
Get LLM provider instance
    │
    ▼
Prepare tools (if enabled)
    │
    ▼
Send to LLM API
    │
    ├──▶ LLM returns response
    │    └─▶ Send to Discord
    │
    └──▶ LLM requests tool call
         │
         ▼
    Execute tool (web search, etc.)
         │
         ▼
    Send tool result to LLM
         │
         ▼
    LLM returns final response
         │
         ▼
    Send to Discord
         │
         ▼
    Log usage & cost
         │
         ▼
    Update database
```

## Component Details

### 1. Configuration Layer

```
config.yaml
    │
    ├─▶ Global settings
    │   ├─ Bot prefix
    │   ├─ Default LLM provider
    │   ├─ Tool configuration
    │   └─ Plugin settings
    │
.env
    │
    └─▶ Secrets
        ├─ Discord token
        ├─ API keys
        └─ Dashboard credentials

SQLite Database
    │
    └─▶ Per-server configuration
        ├─ LLM provider override
        ├─ Model selection
        ├─ Custom prompts
        └─ Usage statistics
```

### 2. LLM Provider System

```
BaseLLMProvider (Interface)
    │
    ├─▶ OpenAIProvider
    │   ├─ GPT-4
    │   ├─ GPT-3.5
    │   └─ Cost calculation
    │
    ├─▶ AnthropicProvider
    │   ├─ Claude 3 Opus
    │   ├─ Claude 3 Sonnet
    │   ├─ Claude 3 Haiku
    │   └─ Cost calculation
    │
    ├─▶ OllamaProvider
    │   ├─ Llama2
    │   ├─ Mistral
    │   └─ Local execution (free)
    │
    └─▶ OpenRouterProvider
        ├─ Multiple models
        └─ Unified interface
```

### 3. Tool System

```
BaseTool (Interface)
    │
    ├─▶ WebSearchTool
    │   ├─ DuckDuckGo
    │   ├─ Google
    │   ├─ Brave
    │   └─ SearxNG
    │
    └─▶ Plugin Tools
        └─ Custom tools from plugins

Tool Execution Flow:
1. LLM decides to use tool
2. Bot receives tool call
3. Execute tool with parameters
4. Return result to LLM
5. LLM incorporates result
6. Final response sent to user
```

### 4. Plugin System

```
Plugin Directory
    │
    ├─▶ plugin_name/
    │   ├─ manifest.json
    │   │   ├─ Name, version
    │   │   ├─ Permissions
    │   │   └─ Tool definitions
    │   │
    │   └─ plugin.py
    │       ├─ Plugin class
    │       ├─ Tool implementations
    │       └─ Cleanup logic
    │
    └─▶ PluginManager
        ├─ Load plugins
        ├─ Check permissions
        ├─ Register tools
        └─ Manage lifecycle
```

### 5. Dashboard

```
Flask Web Server (port 5000)
    │
    ├─▶ Frontend (HTML/CSS/JS)
    │   ├─ Status dashboard
    │   ├─ Configuration UI
    │   ├─ Analytics charts
    │   └─ Server management
    │
    └─▶ REST API
        ├─ GET  /api/status
        ├─ GET  /api/servers
        ├─ POST /api/config
        ├─ GET  /api/usage/stats
        ├─ GET  /api/tools
        └─ GET  /api/providers
```

## Database Schema

```sql
-- Server-specific configurations
server_config
├─ server_id (PK)
├─ llm_provider
├─ llm_model
├─ temperature
├─ max_tokens
├─ system_prompt
├─ enabled_tools
└─ config_json

-- Usage tracking
usage_stats
├─ id (PK)
├─ server_id
├─ user_id
├─ provider
├─ model
├─ tokens_used
├─ cost_usd
└─ timestamp

-- Plugin management
plugins
├─ name (PK)
├─ version
├─ enabled
├─ config_json
└─ installed_at
```

## Security Layers

```
1. Environment Variables
   └─ API keys, tokens never in code

2. Plugin Permissions
   └─ Sandboxed execution
   └─ Permission checks

3. Content Moderation (optional)
   └─ Pre-response filtering
   └─ Policy enforcement

4. Database Access
   └─ Prepared statements
   └─ No SQL injection
```

## Scalability Considerations

```
Conversation Management
├─ In-memory cache
├─ Per-channel isolation
└─ Automatic cleanup

Database
├─ SQLite for small-medium
├─ Can migrate to PostgreSQL
└─ Indexed queries

API Calls
├─ Connection pooling
├─ Rate limiting
├─ Timeout handling
└─ Retry logic

Dashboard
├─ Async endpoints
├─ Caching
└─ Pagination
```

## Extension Points

Users can extend the bot by:

1. **Adding LLM Providers**
   - Implement BaseLLMProvider
   - Register in factory
   - Add to config

2. **Creating Tools**
   - Implement BaseTool
   - Add to tools directory
   - Enable in config

3. **Developing Plugins**
   - Create manifest.json
   - Implement Plugin class
   - Place in plugins/ directory

4. **Customizing Dashboard**
   - Modify templates
   - Add new API endpoints
   - Create custom views

## Technology Stack

```
Core:
├─ Python 3.10+
├─ discord.py (Discord API)
└─ asyncio (Async processing)

LLM Integration:
├─ openai
├─ anthropic
├─ aiohttp (HTTP requests)
└─ ollama

Data Storage:
├─ SQLite (database)
├─ YAML (configuration)
└─ JSON (plugin manifests)

Web Dashboard:
├─ Flask (backend)
├─ HTML/CSS/JS (frontend)
└─ REST API

Utilities:
├─ python-dotenv (env vars)
├─ rich (CLI formatting)
└─ pydantic (data validation)
```

---

This architecture is designed to be:
- **Modular**: Easy to add/remove components
- **Extensible**: Plugin and provider systems
- **Scalable**: Handles multiple servers
- **Maintainable**: Clear separation of concerns
- **Flexible**: Extensive configuration options
