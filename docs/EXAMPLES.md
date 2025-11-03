# Example Configuration Scenarios

This file contains example configurations for different use cases.

## Basic Setup - OpenAI Only

**config.yaml:**
```yaml
bot:
  prefix: "!"
  status: "online"
  activity: "Chatting with GPT-4"

llm:
  default_provider: "openai"
  default_model: "gpt-4-turbo-preview"
  temperature: 0.7
  max_tokens: 2048

tools:
  web_search:
    enabled: true
    default_provider: "duckduckgo"

plugins:
  enabled: false

dashboard:
  enabled: true
  port: 5000
```

**.env:**
```env
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key
```

---

## Multi-Provider Setup

Support multiple LLM providers with per-server customization:

**config.yaml:**
```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-4-turbo-preview"
  
  providers:
    openai:
      enabled: true
      models:
        - gpt-4-turbo-preview
        - gpt-3.5-turbo
    
    anthropic:
      enabled: true
      models:
        - claude-3-opus-20240229
        - claude-3-sonnet-20240229
    
    ollama:
      enabled: true
      base_url: "http://localhost:11434"
      models:
        - llama2
        - mistral
```

**.env:**
```env
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

Then configure per-server via dashboard or database.

---

## Local-Only Setup (Ollama)

Free, runs entirely on your machine:

**config.yaml:**
```yaml
llm:
  default_provider: "ollama"
  default_model: "llama2"
  temperature: 0.8
  
  providers:
    ollama:
      enabled: true
      base_url: "http://localhost:11434"
      models:
        - llama2
        - llama2:13b
        - mistral
        - codellama

tools:
  web_search:
    enabled: true
    default_provider: "duckduckgo"
```

**.env:**
```env
DISCORD_TOKEN=your_discord_token
```

**Requirements:**
- Install Ollama from ollama.ai
- Pull models: `ollama pull llama2`

---

## Content Moderation Enabled

For public servers with strict content policies:

**config.yaml:**
```yaml
bot:
  prefix: "!"
  enable_mentions: true
  enable_dm: false

moderation:
  enabled: true
  provider: "openai"
  model: "text-moderation-latest"
  action_on_violation: "block"
  custom_rules:
    - "No hate speech or harassment"
    - "No personal information sharing"
    - "No NSFW content"
    - "Stay on topic"

llm:
  default_provider: "openai"
  default_model: "gpt-4-turbo-preview"
  temperature: 0.7

prompts:
  system: |
    You are a helpful assistant in a moderated community Discord server.
    Be respectful, inclusive, and professional at all times.
    Do not engage with inappropriate requests.
    If a user asks something inappropriate, politely decline and suggest appropriate topics.
```

---

## Research/Academic Bot

Optimized for research assistance with web search:

**config.yaml:**
```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-4-turbo-preview"
  temperature: 0.3  # Lower for more factual responses
  max_tokens: 3000

tools:
  web_search:
    enabled: true
    default_provider: "brave"  # Or Google for academic focus
    max_results: 10

prompts:
  system: |
    You are an academic research assistant.
    Provide accurate, well-sourced information.
    When answering questions:
    1. Use web search to find current information
    2. Cite sources when possible
    3. Be thorough but concise
    4. Acknowledge uncertainty when appropriate
  
  tool_use: |
    Always use web search for:
    - Recent events or news
    - Scientific papers or studies
    - Statistics or data
    - Current best practices
```

**.env:**
```env
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key
BRAVE_API_KEY=your_brave_key  # Or Google keys
```

---

## Creative Writing Bot

Optimized for creative assistance:

**config.yaml:**
```yaml
llm:
  default_provider: "anthropic"
  default_model: "claude-3-opus-20240229"
  temperature: 0.9  # Higher for creativity
  max_tokens: 4096

prompts:
  system: |
    You are a creative writing assistant.
    Help users brainstorm ideas, develop characters, plot stories, and improve their writing.
    Be imaginative, supportive, and constructive.
    Provide detailed, creative suggestions while respecting the user's vision.

tools:
  web_search:
    enabled: false  # Don't need web search for creative writing
```

---

## Coding Assistant Bot

Specialized for programming help:

**config.yaml:**
```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-4-turbo-preview"
  temperature: 0.2  # Low for precise code

prompts:
  system: |
    You are a programming assistant.
    Help users with:
    - Debugging code
    - Explaining programming concepts
    - Writing code snippets
    - Reviewing code quality
    - Suggesting optimizations
    
    When providing code:
    - Include comments explaining key parts
    - Follow best practices
    - Consider edge cases
    - Use appropriate error handling

tools:
  web_search:
    enabled: true
    default_provider: "duckduckgo"

plugins:
  enabled: true
  allowed_permissions:
    - network
    - storage
```

---

## Multi-Server Bot with Per-Server Settings

Configure different settings for different servers via the database:

**Server 1 (Gaming Community):**
```sql
INSERT INTO server_config (server_id, config_json) VALUES (
  '123456789',
  '{
    "llm_provider": "anthropic",
    "llm_model": "claude-3-sonnet-20240229",
    "temperature": 0.8,
    "system_prompt": "You are a friendly gaming community assistant. Help with game recommendations, strategies, and community events."
  }'
);
```

**Server 2 (Study Group):**
```sql
INSERT INTO server_config (server_id, config_json) VALUES (
  '987654321',
  '{
    "llm_provider": "openai",
    "llm_model": "gpt-4-turbo-preview",
    "temperature": 0.3,
    "system_prompt": "You are an academic tutor. Help students understand concepts, solve problems, and prepare for exams."
  }'
);
```

Or configure via the dashboard at `http://localhost:5000`.

---

## High-Volume Bot (Optimized)

For busy servers with many requests:

**config.yaml:**
```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-3.5-turbo"  # Faster, cheaper

performance:
  cache_enabled: true
  cache_ttl_seconds: 3600
  max_concurrent_requests: 10
  request_timeout_seconds: 30

database:
  backup_enabled: true
  backup_interval_hours: 6

logging:
  level: "WARNING"  # Reduce log verbosity
  max_size_mb: 50
```

---

## Privacy-Focused Setup

Minimal data retention:

**config.yaml:**
```yaml
bot:
  enable_dm: false  # No DMs for privacy

database:
  type: "sqlite"
  backup_enabled: false

logging:
  level: "ERROR"  # Minimal logging

llm:
  default_provider: "ollama"  # Local, private
  default_model: "llama2"

# Don't track usage
```

Modify `src/config/manager.py` to disable usage tracking if desired.

---

## Cost-Conscious Setup

Minimize API costs:

**config.yaml:**
```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-3.5-turbo"  # Cheaper model
  max_tokens: 500  # Limit response length

performance:
  cache_enabled: true
  cache_ttl_seconds: 7200  # Longer cache

# Monitor via dashboard and set alerts
```

Consider switching to Ollama for zero API costs.

---

## Plugin Developer Setup

For testing plugins:

**config.yaml:**
```yaml
plugins:
  enabled: true
  auto_load: true
  allowed_permissions:
    - network
    - storage
    - discord_api
  blocked_imports: []  # Allow all for testing

logging:
  level: "DEBUG"  # Detailed logs
  console_output: true

dashboard:
  enabled: true
```

---

## Temperature Guide

Adjust creativity vs. consistency:

- **0.0 - 0.3**: Factual, consistent, deterministic
  - Use for: Math, code, facts
- **0.4 - 0.7**: Balanced
  - Use for: General chat, help
- **0.8 - 1.2**: Creative, varied
  - Use for: Writing, brainstorming
- **1.3 - 2.0**: Very creative, unpredictable
  - Use for: Experimental, artistic

---

Choose the configuration that best matches your use case and modify as needed!
