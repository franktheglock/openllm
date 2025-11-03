# Testing Plugin Marketplace

## Available Test Plugins

### 1. Calculator Plugin 🧮
**Plugin ID:** `calculator`
**Tool:** `calculate`

A simple math calculator that can evaluate mathematical expressions.

**Example usage:**
- "Calculate 2 + 2"
- "What's 10 * 5 / 2?"
- "Calculate 2 ** 8"

**Features:**
- Basic operations: +, -, *, /
- Power: **
- Modulo: %
- Floor division: //
- Parentheses support
- Safe evaluation (no code execution)

### 2. UUID Generator Plugin 🔑
**Plugin ID:** `uuid_generator`
**Tool:** `generate_uuid`

Generate random UUIDs (Universally Unique Identifiers).

**Example usage:**
- "Generate a UUID"
- "Create 5 random UUIDs"
- "Generate a UUID in hex format"

**Features:**
- UUID4 (random) and UUID1 (timestamp-based)
- Multiple formats: standard, hex, urn
- Generate 1-10 UUIDs at once

## How to Test

### Step 1: Access the Marketplace
1. Start your bot and dashboard
2. Open the dashboard in your browser (http://localhost:5000)
3. Click the "🛒 Plugin Marketplace" button in the header

### Step 2: Install a Plugin
1. Browse the available plugins
2. Click "📦 Install" on the Calculator or UUID Generator plugin
3. Wait for the success message
4. The button should change to "✓ Installed"

### Step 3: Enable Tools in Dashboard
1. Go back to the main dashboard (click "← Back to Dashboard")
2. Make sure the tools are enabled in your bot configuration
3. The tools should be automatically available after installation

### Step 4: Test in Discord
1. Mention your bot in a Discord channel
2. Try these example messages:
   - "@BotName calculate 2 + 2"
   - "@BotName what's 15 * 7?"
   - "@BotName generate a uuid"
   - "@BotName create 3 random UUIDs"

### Step 5: Uninstall (Optional)
You can also test uninstalling:
- The uninstall feature is available via the API: `POST /api/marketplace/uninstall/<plugin_id>`
- This removes the plugin from the database and reloads tools

## Troubleshooting

### Plugin not showing in marketplace
- Check that the plugin folder exists in `plugins/`
- Verify `manifest.json` exists and is valid JSON
- Check browser console for errors

### Tool not available in Discord
- Make sure the plugin is installed (check database or marketplace)
- Restart the bot to reload tools
- Check bot logs for plugin loading errors

### Installation fails
- Check that the `plugins` table exists in the database
- Verify write permissions on the database file
- Check dashboard logs for detailed error messages

## Plugin Structure

Each plugin requires:
```
plugins/
  plugin_name/
    manifest.json    # Plugin metadata
    plugin.py        # Plugin implementation
```

The manifest.json includes:
- name, version, author
- description, icon, category, tags
- tools list
- entry_point (usually plugin.py)

The plugin.py must have:
- Tool class(es) extending BaseTool
- Plugin class with get_tools() and cleanup() methods
