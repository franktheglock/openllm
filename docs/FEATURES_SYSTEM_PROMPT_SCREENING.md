# New Setup Steps: System Prompt & Content Screening

## Summary

Added two new configuration steps to the setup wizard for enhanced bot customization and safety:

1. **System Prompt Configuration** (Step 3) - Define bot personality and behavior
2. **Content Screening** (Step 5) - Optional AI-powered content moderation

The setup wizard now has **6 steps** instead of 4.

---

## Step 3: System Prompt Configuration

### What It Does

Allows you to define how your bot should behave, respond, and interact with users through a customizable system prompt.

### Features

#### Manual Prompt Entry
- Large text area for writing custom system prompts
- Pre-filled with sensible default: "You are a helpful Discord bot assistant. Be friendly, concise, and helpful."
- Supports multi-line prompts with detailed instructions

#### AI Prompt Assistant 💡
- Uses your configured LLM to generate system prompts
- Simply describe what you want your bot to do
- AI generates a professional, well-structured prompt

### UI Layout

```
┌─────────────────────────────────────────────────────┐
│  System Prompt Configuration                       │
│  Define how your bot should behave and respond     │
├─────────────────────────────────────────────────────┤
│  System Prompt:                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Large text area - 150px height]             │ │
│  │ You are a helpful Discord bot assistant...   │ │
│  │                                               │ │
│  └───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  💡 AI Prompt Assistant                            │
│  Describe what you want your bot to do             │
│  ┌────────────────────────────────┐ ┌───────────┐ │
│  │ E.g., 'Make my bot act like... │ │ Generate  │ │
│  └────────────────────────────────┘ └───────────┘ │
│  🤖 Generating prompt... / ✓ Success / ✗ Failed   │
└─────────────────────────────────────────────────────┘
```

### How to Use the AI Assistant

1. **Describe Your Vision**
   ```
   "Make my bot act like a friendly coding mentor who explains 
   concepts clearly and encourages beginners"
   ```

2. **Click "Generate Prompt"**
   - Uses your configured LLM provider (from Step 2)
   - Requires API key (except for Ollama)
   - Takes 2-5 seconds to generate

3. **Review & Edit**
   - Generated prompt appears in the text area
   - You can edit it further
   - Click "Next" to save

### Example Prompts

**Casual & Friendly:**
```
You are a friendly Discord bot who loves helping people. Keep responses 
casual, use emojis occasionally 🎉, and make users feel welcome. Be 
helpful but don't be overly formal.
```

**Professional Assistant:**
```
You are a professional Discord assistant. Provide accurate, well-structured 
responses. Be respectful, concise, and helpful. Focus on solving problems 
efficiently.
```

**Pirate Character:**
```
You are a pirate-themed Discord bot! Arr matey! Respond in pirate speak, 
use sailing metaphors, and keep the seafaring theme alive. Be helpful but 
stay in character.
```

### Configuration Saved To

- **config.yaml**: `llm.system_prompt`
- Used by bot at runtime to set LLM behavior

---

## Step 5: Content Screening (Optional)

### What It Does

Adds an AI-powered safety layer that reviews bot responses before sending them to Discord, helping prevent inappropriate, harmful, or policy-violating content.

### Features

#### Enable/Disable Toggle
- Checkbox to enable content screening
- Optional feature - disabled by default
- Configuration options appear when enabled

#### Screening Model Selection
- Choose a fast, cost-effective model for screening
- Dropdown pre-populated with available models
- Recommended: `gemini-1.5-flash` or `gpt-4o-mini` (fast & cheap)

#### Action on Flagged Content
Three options when content is flagged:

1. **Block and notify user**
   - Prevents message from being sent
   - Sends user a notification that content was blocked
   - Most secure option

2. **Log but allow**
   - Logs the flag to console/logs
   - Allows message to be sent anyway
   - Good for testing/monitoring

3. **Replace with safe message**
   - Blocks original message
   - Sends a generic safe response instead
   - Example: "I cannot provide that response. How else can I help?"

#### Screening Policy
- Text area to define what should be flagged
- Default policy covers:
  - Harmful content
  - Hateful content
  - Explicit content
  - Discord TOS violations
- Fully customizable

### UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Content Screening (Optional)                      │
│  Configure AI-powered content moderation           │
├─────────────────────────────────────────────────────┤
│  ☐ Enable Content Screening                       │
│     Uses AI to review bot responses before sending │
│                                                     │
│  [When enabled, shows:]                            │
│  ┌───────────────────────────────────────────────┐ │
│  │ Screening Model:                              │ │
│  │ Choose a fast, cost-effective model           │ │
│  │ [Dropdown: gemini-1.5-flash ▼]                │ │
│  ├───────────────────────────────────────────────┤ │
│  │ Action on Flagged Content:                    │ │
│  │ ○ Block and notify user                       │ │
│  │ ○ Log but allow                               │ │
│  │ ○ Replace with safe message                   │ │
│  ├───────────────────────────────────────────────┤ │
│  │ Screening Policy:                             │ │
│  │ ┌─────────────────────────────────────────┐   │ │
│  │ │ [Text area - 120px height]              │   │ │
│  │ │ Keep responses safe, respectful, and... │   │ │
│  │ └─────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### How It Works

1. **Bot generates response** using main LLM
2. **Screening LLM reviews** response against policy
3. **If flagged:**
   - **Block**: Don't send, notify user
   - **Log**: Log flag, send anyway
   - **Replace**: Send safe alternative message
4. **If safe:** Send response normally

### Example Policies

**Strict (Family-Friendly):**
```
Keep responses safe, respectful, and appropriate for all ages. Block content 
that contains profanity, violence, adult themes, discrimination, or anything 
that wouldn't be appropriate for a G-rated environment.
```

**Moderate (Discord Standard):**
```
Keep responses safe, respectful, and appropriate for all audiences. Block 
content that is harmful, hateful, explicit, or violates Discord TOS. Allow 
mild language and mature discussions if respectful.
```

**Minimal (Legal Only):**
```
Block only content that is illegal, promotes violence/harm, or severely 
violates Discord's Terms of Service. Allow frank discussions and diverse 
viewpoints.
```

### Performance Considerations

**Cost & Speed:**
- Screening adds ~0.5-2 seconds per response
- Uses additional API calls (1 per bot response)
- Recommended to use cheap models:
  - Gemini Flash: ~$0.00001 per request
  - GPT-4o-mini: ~$0.00015 per request

**When to Enable:**
- Public Discord servers
- Bots accessible to minors
- Corporate/professional environments
- Compliance requirements

**When to Disable:**
- Private/trusted servers
- Development/testing
- Cost constraints
- Speed priority

### Configuration Saved To

- **config.yaml**: 
  - `screening.enabled` - true/false
  - `screening.model` - model to use
  - `screening.action` - block/log/replace
  - `screening.policy` - policy text

---

## Updated Setup Flow

### New 6-Step Process

1. **Discord Configuration** - Token & prefix
2. **AI Provider** - LLM selection & API key
3. **System Prompt** ⭐ NEW - Define bot behavior
4. **Tools & Features** - Web search & dashboard
5. **Content Screening** ⭐ NEW - Optional safety layer
6. **Summary** - Review & finish

### Step Numbers Changed

| Feature | Old Step | New Step |
|---------|----------|----------|
| Discord Config | 1 | 1 ✓ |
| LLM Provider | 2 | 2 ✓ |
| System Prompt | - | **3** 🆕 |
| Tools (Search/Dashboard) | 3 | **4** ⬆️ |
| Content Screening | - | **5** 🆕 |
| Summary | 4 | **6** ⬆️ |

---

## Validation

### System Prompt (Step 3)
- **Required**: Must have non-empty prompt
- Error shown if text area is blank
- Saved from text area (not StringVar)

### Content Screening (Step 5)
- **Only validated if enabled**
- If enabled, policy text must be non-empty
- Model selection required
- Saved from text area (not StringVar)

---

## Code Changes

### Files Modified

**src/setup_wizard_gui.py**
- `total_steps`: 4 → 6
- `setup_data`: Added system_prompt, screening fields
- `show_step()`: Added cases for steps 3 and 5
- `show_system_prompt_step()`: New method
- `generate_system_prompt()`: AI assistant logic
- `show_screening_step()`: New method
- `on_screening_toggle()`: Show/hide config
- `validate_current_step()`: Added validation for steps 3 & 5
- `finish_setup()`: Save new configurations
- `show_final_step()`: Updated summary items

### New Dependencies

- Uses existing LLM providers via `LLMProviderFactory`
- No new package dependencies
- Works with all 5 providers (Gemini, OpenAI, Anthropic, Ollama, OpenRouter)

---

## Example Usage

### Testing System Prompt Generation

```bash
python main.py --reset
```

1. Complete steps 1-2 (Discord & LLM provider)
2. On step 3:
   - Enter: "Make my bot a helpful coding tutor for Python beginners"
   - Click "Generate Prompt"
   - Wait 2-3 seconds
   - Review generated prompt
   - Edit if needed
   - Click "Next"

### Testing Content Screening

1. Complete steps 1-4
2. On step 5:
   - ✓ Enable Content Screening
   - Model: `gemini-1.5-flash`
   - Action: `Block and notify user`
   - Policy: (use default or customize)
   - Click "Next"

---

## Future Enhancements

Possible improvements:

- [ ] Multiple system prompt templates (dropdown presets)
- [ ] System prompt testing (preview bot responses)
- [ ] Screening policy templates (family-friendly, moderate, minimal)
- [ ] Test screening against sample messages
- [ ] Show estimated screening costs
- [ ] Screening statistics dashboard
- [ ] Whitelist/blacklist for screening bypass
- [ ] Custom screening actions (webhooks, logging)

---

## Troubleshooting

### AI Prompt Generation Failed

**Error:** "Could not generate prompt"

**Solutions:**
1. Verify API key is correct in Step 2
2. Check internet connection
3. Try different LLM provider
4. Write prompt manually instead

### Screening Always Blocks

**Problem:** All responses are flagged

**Solutions:**
1. Review screening policy - too strict?
2. Try different screening model
3. Change action to "Log but allow" temporarily
4. Check screening model has proper API access

### Setup Steps Out of Order

**Problem:** Summary shows wrong info

**Solutions:**
1. Use "Back" button to review steps
2. Don't skip steps with "Next"
3. Run `python main.py --reset` to restart

---

## Configuration Reference

### config.yaml Structure

```yaml
llm:
  system_prompt: "You are a helpful Discord bot assistant..."
  default_provider: gemini
  default_model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 2048

screening:
  enabled: false
  model: gemini-1.5-flash
  action: block  # block | log | replace
  policy: "Keep responses safe, respectful, and appropriate..."
```

### Default Values

| Setting | Default Value |
|---------|---------------|
| `system_prompt` | "You are a helpful Discord bot assistant. Be friendly, concise, and helpful." |
| `screening.enabled` | `false` |
| `screening.model` | `gemini-1.5-flash` |
| `screening.action` | `block` |
| `screening.policy` | "Keep responses safe, respectful, and appropriate for all audiences. Block content that is harmful, hateful, explicit, or violates Discord TOS." |

---

## Best Practices

### System Prompts
✅ **Do:**
- Be specific about tone and style
- Include behavior guidelines
- Keep it concise (2-5 sentences)
- Test with real questions

❌ **Don't:**
- Make it too long (>500 words)
- Include contradictory instructions
- Use overly complex language
- Forget to set clear boundaries

### Content Screening
✅ **Do:**
- Start disabled, enable if needed
- Use fast/cheap models for screening
- Test policy with edge cases
- Monitor logs for false positives

❌ **Don't:**
- Use expensive models (GPT-4)
- Make policy too vague
- Block everything (too strict)
- Skip testing before going live
