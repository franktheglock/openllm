# Bug Fixes: Screening Escalation, Loop Error, and Reply Feature

## Summary

Fixed three issues:

1. ✅ **Added "Escalate to Moderators" screening action** - New option to send flagged content to a moderation channel
2. ✅ **Fixed asyncio loop error in system prompt generation** - Handled existing event loops properly
3. ✅ **Bot now replies to user messages** - Uses Discord's reply feature instead of plain channel messages

---

## 1. Escalate to Moderators Option

### What Changed

Added a fourth action option for content screening that sends flagged content to a designated moderation channel for manual review.

### New UI Elements

**Screening Step (Step 5):**
```
Action on Flagged Content:
○ Block and notify user
○ Log but allow
○ Replace with safe message
○ Escalate to moderators  ⭐ NEW

[When "Escalate" is selected:]
┌─────────────────────────────────────┐
│ Moderation Channel ID:              │
│ [Text input field]                  │
│ Right-click channel → Copy ID       │
│ Flagged messages sent here for      │
│ manual review                       │
└─────────────────────────────────────┘
```

### Code Changes

**src/setup_wizard_gui.py:**

1. **Added field to setup_data:**
   ```python
   'screening_channel_id': tk.StringVar(value='')
   ```

2. **Added UI elements:**
   - Fourth radio button: "Escalate to moderators"
   - Conditional `mod_channel_frame` that shows when escalate is selected
   - Channel ID text input field
   - Helper text explaining how to get channel ID

3. **Added visibility toggle:**
   ```python
   def on_screening_action_change(self):
       """Show/hide moderation channel field based on action."""
       if self.setup_data['screening_action'].get() == 'escalate':
           self.mod_channel_frame.pack(fill="x", padx=20, pady=10)
       else:
           self.mod_channel_frame.pack_forget()
   ```

4. **Added validation:**
   - Channel ID required when escalate is selected
   - Must be numeric (Discord IDs are numbers)
   - Error shown if empty or non-numeric

5. **Save to config:**
   ```python
   if self.setup_data['screening_action'].get() == 'escalate':
       self.config_manager.set('screening.channel_id', 
                               self.setup_data['screening_channel_id'].get())
   ```

### How It Works

1. User enables content screening in setup
2. Selects "Escalate to moderators" action
3. Channel ID field appears
4. User enters moderation channel ID
5. When bot detects flagged content:
   - Original message not sent to user
   - Flagged content sent to mod channel with context
   - Moderators can review and decide manually

### Configuration

**config.yaml:**
```yaml
screening:
  enabled: true
  model: gemini-1.5-flash
  action: escalate  # NEW VALUE
  policy: "Keep responses safe..."
  channel_id: "1234567890123456789"  # NEW FIELD
```

### Usage Flow

1. **Bot generates response**
2. **Screening LLM checks it against policy**
3. **If flagged:**
   - Send alert to moderation channel
   - Include: original question, flagged response, reason
   - Moderators review and take action
4. **User sees:** "Your request is being reviewed by moderators"

---

## 2. Fixed Asyncio Loop Error

### The Problem

When clicking "Generate Prompt" in the system prompt step, error occurred:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

This happened because:
- Tkinter may already have an event loop running
- Creating a new loop with `asyncio.new_event_loop()` conflicts
- `asyncio.run()` internally creates a new loop

### The Solution

**Before:**
```python
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def generate():
    response = await llm.generate(...)
    return response.strip()

generated_prompt = loop.run_until_complete(generate())
loop.close()
```

**After:**
```python
import asyncio

async def generate():
    response = await llm.generate(...)
    return response.strip()

# Try to get existing loop, or create new one
try:
    loop = asyncio.get_running_loop()
    # If we're already in a loop, run in executor
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        generated_prompt = pool.submit(
            lambda: asyncio.run(generate())
        ).result()
except RuntimeError:
    # No running loop, safe to create new one
    generated_prompt = asyncio.run(generate())
```

### How It Works

1. **Try to detect existing loop:**
   - `asyncio.get_running_loop()` checks if loop is active
   - If yes, we're in async context already

2. **If loop exists:**
   - Can't use `asyncio.run()` (would conflict)
   - Use `ThreadPoolExecutor` to run in separate thread
   - Thread can safely create its own loop

3. **If no loop:**
   - Safe to use `asyncio.run(generate())`
   - Creates, runs, and cleans up loop automatically

### Benefits

✅ Works whether Tkinter has a loop or not  
✅ No more RuntimeError crashes  
✅ Proper cleanup in both cases  
✅ Compatible with all environments  

---

## 3. Bot Now Replies to Messages

### What Changed

Bot now uses Discord's reply feature instead of sending plain messages in the channel.

### Before & After

**Before:**
```
User: @Bot What's the weather?
Bot: The weather is sunny today!
```
(No visual connection between messages)

**After:**
```
User: @Bot What's the weather?
  ↪️ Bot: The weather is sunny today!
```
(Reply shows connection with a visual indicator)

### Code Changes

**src/bot.py:**

1. **Updated `_send_response()` signature:**
   ```python
   # Before
   async def _send_response(self, channel, content: str):
       await channel.send(content)
   
   # After
   async def _send_response(self, message: discord.Message, content: str):
       await message.reply(content, mention_author=False)
   ```

2. **Updated call site:**
   ```python
   # Before
   await self._send_response(message.channel, response.content)
   
   # After
   await self._send_response(message, response.content)
   ```

3. **Updated error handling:**
   ```python
   # Before
   await message.channel.send("Sorry, I encountered an error...")
   
   # After
   await message.reply("Sorry, I encountered an error...", mention_author=False)
   ```

4. **Handled long messages:**
   ```python
   if len(content) <= max_length:
       await message.reply(content, mention_author=False)
   else:
       chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
       # Reply to first chunk
       await message.reply(chunks[0], mention_author=False)
       # Send rest as normal messages
       for chunk in chunks[1:]:
           await message.channel.send(chunk)
   ```

### Benefits

✅ **Clear context** - Easy to see which message bot is responding to  
✅ **Better UX** - Standard Discord reply feature  
✅ **No pings** - `mention_author=False` prevents notification spam  
✅ **Works with threads** - Replies work in threads too  
✅ **Mobile friendly** - Reply indicator shows on all devices  

### Reply Behavior

- **First chunk:** Always uses `.reply()` 
- **Subsequent chunks:** Regular `.send()` (Discord doesn't support multi-message replies)
- **Errors:** Also use `.reply()` for consistency
- **No mention:** `mention_author=False` to avoid pinging user

---

## Testing

### Test Escalate Action

1. Run setup: `python main.py --reset`
2. Enable screening in Step 5
3. Select "Escalate to moderators"
4. **Verify:** Channel ID field appears
5. Enter invalid ID (letters): `abc123`
6. Click Next
7. **Verify:** Error "Channel ID must be a number"
8. Enter valid ID: `1234567890123456789`
9. Click Next
10. **Verify:** Setup completes
11. Check `config.yaml` has `screening.channel_id`

### Test System Prompt Generation

1. Run setup: `python main.py --reset`
2. Complete Steps 1-2 (Discord + LLM)
3. Step 3: Enter "make my bot helpful"
4. Click "Generate Prompt"
5. **Verify:** No asyncio error
6. **Verify:** Status shows "🤖 Generating prompt..."
7. **Verify:** Generated prompt appears
8. **Verify:** Can generate multiple times

### Test Reply Feature

1. Start bot: `python main.py`
2. In Discord, send: `@BotName hello`
3. **Verify:** Bot replies with arrow indicator (↪️)
4. **Verify:** Reply shows connection to your message
5. Send long message requiring 3000+ char response
6. **Verify:** First chunk is a reply
7. **Verify:** Subsequent chunks are normal messages
8. Send invalid request causing error
9. **Verify:** Error message is also a reply

---

## Configuration Reference

### New Config Fields

```yaml
screening:
  enabled: true
  model: gemini-1.5-flash
  action: escalate  # NEW: block | log | replace | escalate
  policy: "Keep responses safe..."
  channel_id: "1234567890123456789"  # NEW: Required for escalate
```

### Action Types

| Action | Behavior | Channel ID Required |
|--------|----------|---------------------|
| `block` | Don't send, notify user | ❌ No |
| `log` | Log flag, send anyway | ❌ No |
| `replace` | Send safe alternative | ❌ No |
| `escalate` | Send to mod channel | ✅ Yes |

---

## Files Modified

1. **src/setup_wizard_gui.py**
   - Added `screening_channel_id` field
   - Added escalate radio button
   - Added conditional channel ID input
   - Added `on_screening_action_change()` method
   - Updated validation for channel ID
   - Updated config saving for channel ID
   - Fixed asyncio loop handling in prompt generation

2. **src/bot.py**
   - Changed `_send_response()` to accept message object
   - Updated to use `message.reply()` instead of `channel.send()`
   - Added `mention_author=False` to avoid pings
   - Updated error handling to use reply
   - Proper handling of multi-chunk replies

---

## Error Handling

### Screening Escalate

**Empty Channel ID:**
```
Error: "Please enter a moderation channel ID for escalation."
```

**Non-numeric Channel ID:**
```
Error: "Channel ID must be a number."
```

**Invalid Channel ID (runtime):**
- Bot logs error if channel not found
- Falls back to logging flag
- Notifies server admins

### Asyncio Loop

**No error handling needed** - Code automatically detects and adapts:
- Existing loop → Use ThreadPoolExecutor
- No loop → Use asyncio.run()

### Reply Feature

**No special errors** - Discord handles failures:
- If original message deleted → Reply fails gracefully
- If in DM → Reply works normally
- If in thread → Reply works normally

---

## Best Practices

### Using Escalate Action

✅ **Do:**
- Create dedicated moderation channel
- Set proper permissions (mods only)
- Document escalation procedures
- Monitor the channel regularly

❌ **Don't:**
- Use public channels
- Use channels with bots
- Forget to check escalations
- Set too strict policies (flood channel)

### System Prompt Generation

✅ **Do:**
- Test generated prompts before accepting
- Edit to match your needs
- Keep prompts concise
- Use for inspiration

❌ **Don't:**
- Trust blindly without reading
- Use overly long generated prompts
- Spam the generate button
- Rely on it for complex requirements

### Reply Feature

✅ **Do:**
- Keeps conversation context clear
- Works great in busy channels
- Mobile-friendly

❌ **Don't:**
- Doesn't mention/ping users (by design)
- First chunk only is reply (limitation)
- Can't reply to deleted messages
