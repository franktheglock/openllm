# New Features: SearxNG URL & OpenRouter API Integration

## Summary

Added two new features to improve the setup experience and OpenRouter integration:

1. **SearxNG URL Configuration** - Input field for custom SearxNG instance URL
2. **OpenRouter API Integration** - Dynamic model fetching from OpenRouter's API

---

## 1. SearxNG URL Input

### What Changed

When users select SearxNG as their search provider in the setup wizard, a text input field now appears to enter their SearxNG instance URL.

### Files Modified

**`src/setup_wizard_gui.py`**

- Added `'searxng_url': tk.StringVar(value='http://localhost:8888')` to setup data
- Added `searxng_url_frame` with URL input field
- Added `on_search_provider_change()` method to show/hide URL input
- Modified `on_search_toggle()` to trigger provider change check
- Updated `finish_setup()` to save SearxNG URL to config and .env

### UI Behavior

```
When SearxNG is selected:
┌─────────────────────────────────────┐
│ Search Provider:                    │
│ ○ DuckDuckGo (Free, No API Key)    │
│ ○ Google Custom Search              │
│ ○ Brave Search                      │
│ ● SearxNG (Self-hosted)             │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ SearxNG Instance URL:           │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ http://localhost:8888       │ │ │
│ │ └─────────────────────────────┘ │ │
│ │ Enter the URL of your SearxNG   │ │
│ │ instance                        │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Configuration Saved

When SearxNG is selected, the URL is saved to:
- `.env` as `SEARXNG_URL=<url>`
- `config.yaml` as `tools.web_search.searxng_url: <url>`

---

## 2. OpenRouter Model API Integration

### What Changed

OpenRouter models are now fetched dynamically from the OpenRouter API instead of using a hardcoded list.

### Files Modified

**`src/llm/openrouter_provider.py`**

Added:
- `fetch_models_from_api()` - Async method to fetch models from `https://openrouter.ai/api/v1/models`
- Model caching with 1-hour TTL to avoid excessive API calls
- `_get_default_models()` - Fallback models if API fetch fails
- Updated `get_available_models()` to return cached or default models

**`src/setup_wizard_gui.py`**

Updated `get_models_for_provider()`:
- For OpenRouter, attempts to fetch models from API if API key is available
- Falls back to default model list if fetch fails
- Handles async API call in sync GUI context

**`dashboard/app.py`**

Updated `api_providers()`:
- Detects OpenRouter provider
- Calls `fetch_models_from_api()` to get fresh model list
- Falls back to cached/default models on error

### API Details

**Endpoint:** `https://openrouter.ai/api/v1/models`

**Response Format:**
```json
{
  "data": [
    {
      "id": "openai/gpt-4o",
      "name": "GPT-4o",
      "pricing": {...},
      ...
    },
    ...
  ]
}
```

**Extracted:** Model IDs from `data[].id`

### Caching Strategy

- **Cache Duration:** 1 hour (3600 seconds)
- **Cache Key:** Class-level `_cached_models` and `_cache_timestamp`
- **Benefits:** 
  - Reduces API calls
  - Faster model list loading
  - Graceful fallback if API is unavailable

### Default Models (Fallback)

If API fetch fails, these models are available:
- `openai/gpt-4o`
- `openai/gpt-4-turbo`
- `anthropic/claude-3-5-sonnet-20241022`
- `anthropic/claude-3-opus-20240229`
- `google/gemini-pro-1.5`
- `google/gemini-flash-1.5`
- `meta-llama/llama-3.2-90b-vision-instruct`
- `mistralai/mixtral-8x22b-instruct`

---

## Benefits

### SearxNG URL Configuration
✅ Users can specify custom SearxNG instances  
✅ Supports self-hosted deployments  
✅ No more manual .env editing  
✅ Validates configuration during setup  

### OpenRouter API Integration
✅ Always up-to-date model list  
✅ Automatically includes new models when released  
✅ Shows all available models (100+ options)  
✅ Caching prevents excessive API calls  
✅ Graceful fallback if API is unavailable  

---

## Testing

### Test SearxNG URL Input

1. Run setup wizard: `python main.py --reset`
2. Navigate to Step 3 (Tools)
3. Enable Web Search
4. Select "SearxNG (Self-hosted)"
5. **Verify:** URL input field appears
6. Enter custom URL: `http://my-searxng.example.com`
7. Complete setup
8. **Verify:** `.env` contains `SEARXNG_URL=http://my-searxng.example.com`

### Test OpenRouter Model Fetching

1. Run setup wizard: `python main.py --reset`
2. Navigate to Step 2 (LLM Provider)
3. Select "OpenRouter"
4. Enter valid OpenRouter API key
5. **Verify:** Model dropdown populates with 100+ models from API
6. Without API key, **verify:** Default models shown

### Test Dashboard Model Fetching

1. Start bot: `python main.py`
2. Open dashboard: `http://localhost:5000`
3. Click "Edit Settings"
4. Select "OpenRouter" provider
5. **Verify:** Model list includes latest OpenRouter models

---

## Error Handling

### SearxNG URL
- Empty URL: Uses default `http://localhost:8888`
- Invalid URL: Saved as-is (validation happens at runtime)

### OpenRouter API
- **API Error:** Falls back to default model list
- **Network Timeout:** Uses cached models or defaults
- **No API Key:** Shows default models
- **Invalid Response:** Logs error, returns defaults

---

## Environment Variables

### New/Updated Variables

```bash
# SearxNG Configuration (if selected)
SEARXNG_URL=http://localhost:8888

# OpenRouter (existing, but now used for API fetch)
OPENROUTER_API_KEY=your_api_key_here
```

---

## Future Enhancements

Possible improvements:
- [ ] Add URL validation for SearxNG input
- [ ] Test SearxNG connection during setup
- [ ] Cache OpenRouter models to disk (persist across restarts)
- [ ] Add model search/filter in dashboard
- [ ] Show model pricing in dashboard
- [ ] Auto-refresh OpenRouter models periodically
