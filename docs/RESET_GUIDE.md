# Reset Functionality - Quick Reference

## Overview
Added `--reset` flag to `main.py` for easy configuration reset during development and testing.

## Usage

```bash
python main.py --reset
```

## What It Does

1. **Deletes configuration files:**
   - `.env` (environment variables)
   - `config.yaml` (bot configuration)
   - `bot_database.db` (legacy database if exists)
   - `data/` directory (SQLite database and related files)

2. **Clears Python cache:**
   - `__pycache__/` in project root
   - `src/__pycache__/` 

3. **Automatically runs setup wizard:**
   - GUI setup wizard launches after reset
   - Allows fresh configuration from scratch

## Use Cases

### Development Testing
Test the setup wizard after making changes:
```bash
python main.py --reset
```

### Switching Providers
Quickly switch from one LLM provider to another:
```bash
python main.py --reset
# Select different provider in wizard
```

### Clean Slate
Start fresh after configuration issues:
```bash
python main.py --reset
```

### Reproducing First-Run
Test the new user experience:
```bash
python main.py --reset
```

## Testing the Feature

Run the test script to check current configuration status:
```bash
python tests/test_reset.py
```

This will show:
- Which config files exist
- File sizes
- Whether bot is configured
- Available test commands

## Safety Notes

⚠️ **Warning:** `--reset` permanently deletes:
- All configuration settings
- Database with usage statistics
- Server-specific configurations
- Plugin data stored in database

💡 **Tip:** Backup important data before resetting:
```bash
# Windows
copy .env .env.backup
copy config.yaml config.yaml.backup
xcopy data data_backup\ /E /I

# Linux/Mac
cp .env .env.backup
cp config.yaml config.yaml.backup
cp -r data data_backup
```

## Modified Files

1. **main.py**
   - Added `--reset` argument
   - Added `reset_configuration()` function
   - Integrated with setup wizard flow

2. **src/config/manager.py**
   - Updated `is_configured()` to check for Gemini API key

3. **README.md**
   - Added Development & Testing section
   - Documented reset command

4. **docs/DEVELOPMENT.md** (NEW)
   - Comprehensive development guide
   - Reset functionality explained
   - Workflow tips

5. **tests/test_reset.py** (NEW)
   - Test script to verify reset works
   - Shows current configuration status

## Related Commands

```bash
# Run setup without resetting
python main.py --setup

# Normal start (checks if configured)
python main.py

# Start without dashboard
python main.py --no-dashboard

# Custom config file
python main.py --config custom.yaml
```

## Integration with Setup Wizard

The reset flow:
1. User runs `python main.py --reset`
2. `reset_configuration()` deletes files
3. Logs confirmation messages
4. Sets `args.setup = True`
5. `ConfigManager.is_configured()` returns `False`
6. GUI setup wizard launches
7. User configures bot from scratch
8. New `.env` and `config.yaml` created
9. Bot starts normally

## Future Enhancements

Possible improvements:
- [ ] Add confirmation prompt before reset
- [ ] Option to backup before reset (`--reset --backup`)
- [ ] Selective reset (only reset database, keep .env, etc.)
- [ ] Reset via dashboard UI
- [ ] Export/import configuration feature
