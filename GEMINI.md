# Gemini Code Assistant Context

## Project Overview

This project is a powerful and extensible Discord bot that integrates with various Large Language Models (LLMs) to provide intelligent conversation, tool usage, and assistance. It features a modern web-based dashboard for configuration and monitoring, and a flexible plugin system for adding new capabilities.

The bot is built with Python, using the `discord.py` library for Discord integration and Flask for the web dashboard. It supports a wide range of LLM providers, including Google Gemini, OpenAI, Anthropic, and local models via Ollama and LM Studio.

## Key Technologies

*   **Backend:** Python
*   **Discord Integration:** `discord.py`
*   **Web Dashboard:** Flask
*   **LLM Providers:**
    *   Google Gemini
    *   OpenAI
    *   Anthropic
    *   Ollama
    *   OpenRouter
    *   LM Studio
    *   Custom OpenAI-compatible endpoints
*   **Database:** SQLite
*   **Configuration:** YAML and `.env` files
*   **Containerization:** Docker

## Project Structure

The project is organized into the following main directories:

*   `src/`: Core source code for the bot, including LLM provider integrations, tool handling, and plugin management.
*   `dashboard/`: The Flask application for the web dashboard.
*   `plugins/`: Directory for plugins that extend the bot's functionality.
*   `docs/`: Project documentation.
*   `data/`: Location for the SQLite database and other persistent data.

## Building and Running

### Quick Start

*   **Windows:** Run `start.bat`
*   **Linux/macOS:** Run `start.sh` or `start_macos.sh`

### Manual Setup

1.  Create a Python virtual environment.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the setup wizard: `python main.py --setup`
4.  Start the bot: `python main.py`

### Docker

The project can also be run using Docker with the provided `docker-compose.yml` file:

```bash
docker-compose up -d
```

## Development Conventions

*   **Code Style:** The project follows the PEP 8 style guide for Python code.
*   **Type Hinting:** Type hints are used throughout the codebase for clarity and static analysis.
*   **Documentation:** Docstrings are used for modules, classes, and functions. The `docs/` directory contains more detailed documentation.
*   **Plugin Development:** The `docs/PLUGIN_DEVELOPMENT.md` file provides a comprehensive guide for creating new plugins. Plugins consist of a `manifest.json` file and a `plugin.py` file.
*   **Testing:** The project includes a `tests/` directory, but it is currently sparse. Contributions to testing are welcome.
*   **Contributions:** The `CONTRIBUTING.md` file outlines the process for contributing to the project, including reporting bugs, suggesting features, and submitting pull requests.
