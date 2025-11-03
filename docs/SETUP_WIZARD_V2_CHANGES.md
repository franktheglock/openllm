# Setup Wizard Enhancement - System Prompt & Content Screening

## Changes Made

### 1. Updated Setup Wizard Structure
- **Total Steps**: 4 → **6 steps**
- Added Step 3: System Prompt Configuration
- Added Step 5: Content Screening Configuration
- Renumbered existing steps 3-4 to 4-6

### 2. New Configuration Fields

Added to `setup_data`:
```python
'system_prompt': tk.StringVar(value='You are a helpful Discord bot assistant. Be friendly, concise, and helpful.')
'enable_screening': tk.BooleanVar(value=False)
'screening_model': tk.StringVar(value='gemini-1.5-flash')
'screening_action': tk.StringVar(value='block')
'screening_policy': tk.StringVar(value='Keep responses safe, respectful, and appropriate for all audiences. Block content that is harmful, hateful, explicit, or violates Discord TOS.')
```

### 3. Step 3: System Prompt Configuration

**Features:**
- Large text area (150px) for custom system prompt
- Pre-filled with sensible default
- **AI Prompt Assistant** - Generate prompts using your LLM
  - Text input for user description
  - "Generate Prompt" button
  - Uses LLMProviderFactory with configured provider
  - Shows status (generating/success/failed)
  - Generated prompt populates text area

**Code Added:**
- `show_system_prompt_step()` - UI layout
- `generate_system_prompt()` - AI generation logic
  - Validates API key is configured
  - Creates provider instance
  - Sends generation request
  - Updates text area with result
  - Error handling with user feedback

### 4. Step 5: Content Screening Configuration

**Features:**
- Enable/disable checkbox (default: disabled)
- Model selection dropdown (uses same provider models)
- Action on flagged content:
  - Block and notify user
  - Log but allow
  - Replace with safe message
- Screening policy text area (120px)
- Conditional display (hidden when disabled)

**Code Added:**
- `show_screening_step()` - UI layout
- `on_screening_toggle()` - Show/hide config frame
- Validation for required fields when enabled

### 5. Updated Validation

`validate_current_step()` now checks:

**Step 2 (System Prompt):**
- Reads text from `system_prompt_text` textbox
- Validates non-empty
- Saves to `setup_data['system_prompt']`

**Step 4 (Screening):**
- Only validates if screening enabled
- Reads text from `screening_policy_text` textbox
- Validates non-empty
- Saves to `setup_data['screening_policy']`

### 6. Updated Configuration Saving

`finish_setup()` now saves:

**To config.yaml:**
```python
self.config_manager.set('llm.system_prompt', self.setup_data['system_prompt'].get())
self.config_manager.set('screening.enabled', self.setup_data['enable_screening'].get())
if self.setup_data['enable_screening'].get():
    self.config_manager.set('screening.model', self.setup_data['screening_model'].get())
    self.config_manager.set('screening.action', self.setup_data['screening_action'].get())
    self.config_manager.set('screening.policy', self.setup_data['screening_policy'].get())
```

**To .env:**
- System prompt saved to config.yaml only (not .env)
- Screening settings saved to config.yaml only

### 7. Updated Summary Step

Added to final summary:
- AI Model
- System Prompt (Configured ✓)
- Content Screening (Enabled/Disabled)

---

## File Changes

**Modified:**
- `src/setup_wizard_gui.py` (major changes)

**Created:**
- `docs/FEATURES_SYSTEM_PROMPT_SCREENING.md` (documentation)

---

## Testing Steps

### Test System Prompt

1. Run: `python main.py --reset`
2. Complete steps 1-2 (Discord & LLM)
3. **Step 3: System Prompt**
   - Default prompt should be visible
   - Enter in AI Assistant: "Make my bot a pirate"
   - Click "Generate Prompt"
   - Verify: Status shows "🤖 Generating prompt..."
   - Verify: Generated prompt appears in text area
   - Verify: Can edit the prompt
   - Click "Next"
4. Complete remaining steps
5. Check `config.yaml` has `llm.system_prompt`

### Test Content Screening

1. Run: `python main.py --reset`
2. Complete steps 1-4
3. **Step 5: Content Screening**
   - Verify: Config frame is hidden initially
   - Check "Enable Content Screening"
   - Verify: Config frame appears
   - Select model: `gemini-1.5-flash`
   - Select action: "Block and notify user"
   - Edit policy text if desired
   - Uncheck "Enable Content Screening"
   - Verify: Config frame hides
   - Re-check to enable
   - Click "Next"
4. **Step 6: Summary**
   - Verify: "Content Screening: Enabled" shown
5. Click "Finish"
6. Check `config.yaml` has `screening.*` settings

### Test Validation

1. **System Prompt Empty:**
   - Delete all text in system prompt text area
   - Click "Next"
   - Verify: Error shown "Please enter a system prompt."

2. **Screening Policy Empty:**
   - Enable screening
   - Delete all text in policy text area
   - Click "Next"
   - Verify: Error shown "Please enter a screening policy."

3. **Screening Disabled:**
   - Disable screening
   - Leave policy empty
   - Click "Next"
   - Verify: No error (validation skipped)

---

## Implementation Notes

### AI Prompt Generation

**How it works:**
1. Gets user's description from entry field
2. Validates LLM provider and API key configured
3. Creates temporary LLM instance using `LLMProviderFactory`
4. Sends meta-prompt asking for system prompt
5. Runs async generation in sync context using `asyncio.new_event_loop()`
6. Updates text area with generated result
7. Handles errors gracefully with user feedback

**Meta-prompt used:**
```
You are a helpful assistant that creates system prompts for Discord bots.
The user wants their bot to: {user_request}

Create a clear, concise system prompt (2-4 sentences) that defines the 
bot's personality, tone, and behavior. The prompt should be professional 
and suitable for a Discord bot.

Respond with ONLY the system prompt text, nothing else.
```

### Conditional UI Display

**System Prompt:**
- Always visible (required step)
- AI Assistant is optional feature

**Screening:**
- Main checkbox always visible
- Config frame uses `pack_forget()` when disabled
- `on_screening_toggle()` called on checkbox change
- Re-packs with same parameters when enabled

### Error Handling

**AI Generation:**
- No API key → Show error, return early
- Generation fails → Catch exception, show error dialog
- Network timeout → Handled by LLM provider
- Invalid response → Try/catch prevents crash

**Validation:**
- Step 3: Always validates system prompt
- Step 5: Only validates if screening enabled
- Text read from textbox widgets (not StringVars)
- `.strip()` used to detect empty/whitespace-only

---

## Next Steps (Not Implemented)

These features could be added later:

1. **System Prompt Templates**
   - Dropdown with presets (Casual, Professional, Technical, etc.)
   - Load template into text area
   - User can customize from there

2. **Prompt Testing**
   - "Test Prompt" button
   - Show preview of bot response with current prompt
   - Helps users verify behavior before finishing

3. **Screening Policy Templates**
   - Similar to system prompt templates
   - Presets: Strict, Moderate, Minimal
   - Helps users choose appropriate level

4. **Screening Test**
   - "Test Policy" button
   - User enters sample message
   - Shows if it would be flagged
   - Helps tune policy sensitivity

5. **Cost Estimation**
   - Calculate estimated cost per message with screening
   - Show in UI to help users decide
   - Based on chosen models and pricing

---

## Configuration Schema

### New Config Structure

```yaml
bot:
  prefix: "!"

llm:
  default_provider: gemini
  default_model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 2048
  system_prompt: "You are a helpful Discord bot assistant. Be friendly, concise, and helpful."  # NEW

screening:  # NEW SECTION
  enabled: false
  model: gemini-1.5-flash
  action: block  # Options: block, log, replace
  policy: "Keep responses safe, respectful, and appropriate for all audiences..."
```

### Config Access

```python
from src.config.manager import ConfigManager

config = ConfigManager()

# Get system prompt
prompt = config.get('llm.system_prompt', default='You are a helpful assistant.')

# Check if screening enabled
if config.get('screening.enabled', default=False):
    model = config.get('screening.model')
    action = config.get('screening.action')
    policy = config.get('screening.policy')
```

---

## All Done! ✓

The setup wizard now includes:
✅ System prompt configuration with AI assistant
✅ Content screening configuration
✅ 6-step setup flow
✅ Proper validation
✅ Configuration saving
✅ Documentation

Ready to test with `python main.py --reset`
