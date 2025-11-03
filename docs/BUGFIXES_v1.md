# Bug Fixes - Version 1.0

## Issues Fixed

### 1. ✅ Added SearxNG to Web Search Options
**Issue:** SearxNG was not listed in the setup wizard web search provider options.

**Fix:** Added SearxNG as the fourth option in `src/setup_wizard_gui.py`:
```python
search_providers = [
    ("DuckDuckGo (Free, No API Key)", "duckduckgo"),
    ("Google Custom Search", "google"),
    ("Brave Search", "brave"),
    ("SearxNG (Self-hosted)", "searxng"),  # NEW
]
```

**Location:** Line 366 in `src/setup_wizard_gui.py`

---

### 2. ✅ Added Model Selection to Setup Wizard
**Issue:** No model configuration during the setup process - users couldn't choose which specific model to use.

**Fix:** 
- Added `llm_model` to setup data storage
- Created model selection combobox with provider-specific models
- Added `get_models_for_provider()` method with comprehensive model lists:
  - **Gemini:** gemini-1.5-flash, gemini-1.5-pro, gemini-pro
  - **OpenAI:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
  - **Anthropic:** claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.
  - **Ollama:** llama3.2, llama3.1, llama2, mistral, codellama
  - **OpenRouter:** Various models from multiple providers

- Model dropdown updates automatically when provider changes
- Selected model is saved to both `.env` and `config.yaml`

**Changes:**
```python
# Added to __init__
'llm_model': tk.StringVar(value='gemini-1.5-flash'),

# Added to show_llm_step()
self.model_combo = ctk.CTkComboBox(
    self.model_frame,
    variable=self.setup_data['llm_model'],
    values=self.get_models_for_provider('gemini'),
    width=500
)

# Updated on_provider_change() to update model list
if hasattr(self, 'model_combo'):
    models = self.get_models_for_provider(provider)
    self.model_combo.configure(values=models)
    if models:
        self.setup_data['llm_model'].set(models[0])
```

**Location:** `src/setup_wizard_gui.py` lines 28, 282-305, 492-495

---

### 3. ✅ Dashboard Model Field Now Supports Text Input
**Issue:** Model field in dashboard was dropdown-only with no support for custom/new model names.

**Fix:** Replaced `<select>` with `<input type="text">` using HTML5 datalist for autocomplete:

**Before:**
```html
<select id="modelSelect" class="form-control">
    <option value="">Select provider first...</option>
</select>
```

**After:**
```html
<input type="text" id="modelInput" class="form-control" list="modelOptions" 
       placeholder="Select or type custom model name">
<datalist id="modelOptions">
    <option value="">Loading...</option>
</datalist>
<small style="color: #6b7280;">Select from dropdown or type a custom model name</small>
```

**Benefits:**
- Users can select from suggested models (dropdown behavior)
- Users can type custom model names (text input)
- Perfect for new models released after bot deployment
- Supports experimental/preview models

**JavaScript changes:**
- Updated `updateModelSelect()` to populate datalist instead of select
- Changed `saveConfig()` to read from `modelInput` instead of `modelSelect`
- Variable changed from `select` to `input`/`datalist`

**Location:** `dashboard/templates/index.html` lines 393-399, 568-583, 654

---

### 4. ✅ Fixed GUI Wizard Window Size
**Issue:** Setup wizard window opened too small (800x600), causing content cutoff and making text/buttons hard to read.

**Fix:** Increased window size and added minimum size constraint:

**Before:**
```python
self.geometry("800x600")
```

**After:**
```python
self.geometry("900x700")
self.minsize(850, 650)  # Set minimum size to prevent cutoff
```

**Benefits:**
- More comfortable reading experience
- All content visible without scrolling
- Window can't be resized too small (prevents accidental cutoff)
- Better spacing for all wizard steps

**Location:** `src/setup_wizard_gui.py` line 27

---

## Testing

All fixes have been tested and verified:

✅ SearxNG appears in web search provider list  
✅ Model selection works in setup wizard  
✅ Model dropdown auto-updates when provider changes  
✅ Dashboard model field accepts custom input  
✅ Dashboard model field shows suggestions from datalist  
✅ Window size is adequate for all content  
✅ Window has minimum size constraint  

## Files Modified

1. **src/setup_wizard_gui.py**
   - Added SearxNG to search providers
   - Added model selection UI and logic
   - Increased window size and added minsize
   - Updated configuration save logic

2. **dashboard/templates/index.html**
   - Changed model select to text input with datalist
   - Updated JavaScript to handle text input
   - Added helper text for users

## Upgrade Notes

No breaking changes. Existing configurations will continue to work.

If you have an existing `.env` or `config.yaml`:
- Run `python main.py --reset` to reconfigure with new model selection
- Or manually add `DEFAULT_MODEL=gemini-1.5-flash` to your `.env`

## Related Issues

These fixes address user feedback about:
- Missing search provider options
- Lack of model configuration
- Inflexible model selection in dashboard
- UI usability (window too small)
