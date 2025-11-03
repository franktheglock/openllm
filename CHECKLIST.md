# Pre-Launch Checklist

Use this checklist before deploying your Discord LLM Bot.

## Prerequisites

- [ ] Python 3.10+ installed
- [ ] Discord bot created at [Discord Developer Portal](https://discord.com/developers/applications)
- [ ] At least one LLM API key obtained
- [ ] Bot invited to your Discord server

## Installation

- [ ] Project downloaded/cloned
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)

## Configuration

### Discord Setup
- [ ] Discord bot token copied
- [ ] MESSAGE CONTENT INTENT enabled in Developer Portal
- [ ] SERVER MEMBERS INTENT enabled (optional)
- [ ] Bot has necessary permissions in Discord server:
  - [ ] Read Messages/View Channels
  - [ ] Send Messages
  - [ ] Read Message History

### Environment Variables (.env)
- [ ] `.env` file created from `.env.example`
- [ ] `DISCORD_TOKEN` set
- [ ] At least one LLM provider API key set:
  - [ ] `OPENAI_API_KEY` (if using OpenAI)
  - [ ] `ANTHROPIC_API_KEY` (if using Anthropic)
  - [ ] `OPENROUTER_API_KEY` (if using OpenRouter)
  - [ ] Ollama installed and running (if using local models)

### Web Search (Optional)
- [ ] Search provider chosen
- [ ] API keys configured (if not using DuckDuckGo):
  - [ ] `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` (for Google)
  - [ ] `BRAVE_API_KEY` (for Brave)
  - [ ] `SEARXNG_URL` (for SearxNG)

### Configuration File
- [ ] `config.yaml` exists and is valid
- [ ] Default LLM provider set correctly
- [ ] Default model specified
- [ ] Temperature and max_tokens configured
- [ ] Tools enabled/disabled as desired
- [ ] System prompts customized (optional)

## First Run

- [ ] Setup wizard completed (`python main.py --setup`)
- [ ] Bot starts without errors
- [ ] Database created (`data/bot.db` exists)
- [ ] Logs directory created (`logs/`)
- [ ] Bot shows "logged in" message

## Testing

### Basic Functionality
- [ ] Bot appears online in Discord
- [ ] Bot responds to mentions (`@BotName hello`)
- [ ] Bot responds to prefix commands (`!hello`)
- [ ] Responses are relevant and coherent
- [ ] Conversation context is maintained

### Tools
- [ ] Web search tool works (if enabled)
- [ ] Tool results are incorporated into responses
- [ ] No errors when using tools

### Dashboard
- [ ] Dashboard accessible at `http://localhost:5000`
- [ ] Bot status shows "Online"
- [ ] Connected servers listed
- [ ] Usage statistics visible
- [ ] Tools and providers listed correctly

### Configuration
- [ ] Server-specific settings work (if configured)
- [ ] Different settings for different servers (if applicable)
- [ ] Configuration changes persist after restart

## Security

- [ ] `.env` file is in `.gitignore`
- [ ] API keys are not exposed in logs
- [ ] Dashboard is not publicly accessible (or secured)
- [ ] Bot permissions are minimal necessary
- [ ] Content moderation enabled (if in public servers)

## Performance

- [ ] Response time is acceptable (< 10 seconds typically)
- [ ] No memory leaks after extended use
- [ ] Database size is reasonable
- [ ] Logs are rotating properly

## Documentation

- [ ] README.md reviewed
- [ ] Setup guide followed (`docs/SETUP.md`)
- [ ] Configuration examples reviewed (`docs/EXAMPLES.md`)
- [ ] Team members know how to use the bot

## Production Deployment (if applicable)

- [ ] Bot running as a service/daemon
- [ ] Auto-restart on failure configured
- [ ] Backups configured for database
- [ ] Monitoring/alerting set up
- [ ] Rate limiting considered
- [ ] Cost monitoring in place

## Optional Features

### Plugins
- [ ] Plugin system enabled (if using)
- [ ] Plugins loaded and working
- [ ] Plugin permissions configured correctly

### Moderation
- [ ] Content moderation enabled (if needed)
- [ ] Moderation rules configured
- [ ] Test cases passed

### Advanced Configuration
- [ ] Multiple LLM providers configured
- [ ] Per-server customization implemented
- [ ] Custom tools developed (if needed)
- [ ] Analytics reviewed

## Common Issues Checked

- [ ] All import errors resolved
- [ ] No missing dependencies
- [ ] Database permissions correct
- [ ] Firewall allows dashboard port (if remote access needed)
- [ ] Token budget sufficient for expected usage
- [ ] API rate limits understood

## Final Verification

- [ ] Bot has been running stable for at least 1 hour
- [ ] Multiple conversations tested
- [ ] Different servers tested (if multi-server)
- [ ] Error logs reviewed (should be minimal)
- [ ] Performance is acceptable
- [ ] Cost per request is reasonable

## Support Preparation

- [ ] Logs accessible for debugging
- [ ] Configuration backed up
- [ ] Documentation bookmarked
- [ ] Support contacts identified
- [ ] Rollback plan prepared

---

## Deployment Checklist Score

Count your checkmarks:
- **All checked**: Ready for production! 🚀
- **90%+ checked**: Almost there, review unchecked items
- **80-90% checked**: Good progress, but more testing needed
- **< 80% checked**: Not ready, complete remaining items

---

## Post-Deployment

After 24 hours of operation:
- [ ] Review usage statistics
- [ ] Check for any errors in logs
- [ ] Verify cost is within budget
- [ ] Collect user feedback
- [ ] Adjust configuration as needed

After 1 week:
- [ ] Review total costs
- [ ] Analyze usage patterns
- [ ] Optimize configuration
- [ ] Update documentation if needed
- [ ] Plan any enhancements

---

**Date Completed**: _______________  
**Deployed By**: _______________  
**Version**: 1.0.0  

Good luck with your Discord LLM Bot! 🎉
