# Contributing to Discord LLM Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features
- 🔌 Create plugins
- 🧪 Write tests

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/discord-llm-bot.git
   cd discord-llm-bot
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable names

### Example

```python
def process_message(message: str, max_length: int = 2000) -> str:
    """
    Process a Discord message.
    
    Args:
        message: The message content
        max_length: Maximum message length
    
    Returns:
        Processed message
    """
    # Implementation
    pass
```

## Testing

Before submitting a pull request:

1. Test your changes thoroughly
2. Ensure the bot starts without errors
3. Test with different configurations
4. Check that existing features still work

## Documentation

When adding new features:

- Update relevant documentation files
- Add examples if applicable
- Update README.md if needed
- Comment complex code sections

## Pull Request Process

1. Update your branch with the latest main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request with:
   - Clear description of changes
   - Screenshots/examples if applicable
   - Reference to related issues
   - List of breaking changes (if any)

4. Wait for review and address feedback

## Plugin Development

If contributing a plugin:

1. Follow the [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md)
2. Include a README.md in your plugin directory
3. Test thoroughly before submitting
4. Document required permissions
5. Provide usage examples

## Reporting Bugs

When reporting bugs, include:

- Bot version
- Python version
- Operating system
- Steps to reproduce
- Expected vs. actual behavior
- Error messages/logs
- Configuration (sanitized, no API keys!)

## Suggesting Features

For feature requests:

- Explain the use case
- Describe expected behavior
- Provide examples if possible
- Discuss potential implementation

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and improve
- Focus on the issue, not the person

## Questions?

- Open an issue for discussion
- Check existing issues and PRs
- Review documentation first

Thank you for contributing! 🎉
