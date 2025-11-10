"""Web-based setup wizard for OpenLLM.

Provides a multi-step web experience that mirrors the dashboard styling
and persists configuration to both the YAML config and .env file.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import subprocess
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request
from dotenv import set_key
from werkzeug.serving import make_server

from src.config.manager import ConfigManager
from src.llm.factory import LLMProviderFactory
from src.llm.base import Message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT_DIR / "dashboard" / "templates"
DEFAULT_ENV_EXAMPLE = ROOT_DIR / ".env.example"
# Default env file location inside project root (installed binary dir)
DEFAULT_ENV = ROOT_DIR / ".env"

# Fallback per-user directory for writable runtime configuration. Use LOCALAPPDATA
# when available, otherwise fall back to the user's home directory.
USER_CONFIG_DIR = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "OpenLLM"


PROVIDER_MODELS: Dict[str, list[str]] = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    "openai": ["gpt-5", "gpt-5-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "ollama": ["granite4:3b", "llama3.2", "mistral", "phi3", "codellama"],
    "openrouter": [
        "openai/gpt-4o",
        "openai/gpt-4-turbo",
        "anthropic/claude-3-5-sonnet-20241022",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3.2-90b-vision-instruct",
        "Type custom model name...",
    ],
}

RECOMMENDED_PROMPT = (
    "You are a helpful Discord bot assistant. Be friendly, concise, and helpful."
)

OLLAMA_GUIDE = {
    "linux_command": "curl -fsSL https://ollama.com/install.sh | sh",
    "windows_download": "https://ollama.ai/download",
    "mac_download": "https://ollama.ai/download",
    "start_server": "ollama serve",
    "pull_model": "ollama pull granite4:3b",
    "run_model": "ollama run granite4:3b",
}


@dataclass
class SetupOptions:
    allow_launch: bool = False
    auto_start_dashboard: bool = False
    completion_event: Optional[threading.Event] = None


def _ensure_env_file() -> Path:
    """Ensure a .env file exists by copying from example if available."""
    # Try to create/use the env file inside the installation/root directory first.
    try:
        if not DEFAULT_ENV.exists():
            if DEFAULT_ENV_EXAMPLE.exists():
                DEFAULT_ENV.write_text(DEFAULT_ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                DEFAULT_ENV.touch()
        return DEFAULT_ENV
    except PermissionError:
        # Likely installed under Program Files - fall back to per-user config directory
        try:
            USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            user_env = USER_CONFIG_DIR / ".env"
            if not user_env.exists():
                if DEFAULT_ENV_EXAMPLE.exists():
                    # Copy example into per-user config dir
                    user_env.write_text(DEFAULT_ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
                else:
                    user_env.touch()
            return user_env
        except Exception:
            # As a last resort, re-raise the original PermissionError to preserve behavior
            raise


def _set_env_value(env_path: Path, key: str, value: Any) -> None:
    """Persist an environment variable to the .env file and current process."""
    value_str = "" if value is None else str(value)
    set_key(str(env_path), key, value_str)
    os.environ[key] = value_str


def _serialize_config(config: ConfigManager) -> Dict[str, Any]:
    """Return a normalized snapshot of current configuration and env."""
    env = os.environ
    cfg = config.config

    dashboard_cfg = cfg.get("dashboard", {}) if isinstance(cfg, dict) else {}
    tools_cfg = cfg.get("tools", {}) if isinstance(cfg, dict) else {}
    web_search_cfg = tools_cfg.get("web_search", {}) if isinstance(tools_cfg, dict) else {}
    screening_cfg = cfg.get("screening", {}) if isinstance(cfg, dict) else {}

    data = {
        "discordTokenSet": bool(env.get("DISCORD_TOKEN") and env.get("DISCORD_TOKEN") != "your_discord_bot_token_here"),
        "prefix": env.get("DISCORD_PREFIX") or cfg.get("bot", {}).get("prefix", "!"),
        "provider": cfg.get("llm", {}).get("default_provider", env.get("DEFAULT_LLM_PROVIDER", "gemini")),
        "model": cfg.get("llm", {}).get("default_model", env.get("DEFAULT_MODEL", "gemini-2.5-flash")),
        "temperature": cfg.get("llm", {}).get("temperature", 0.7),
        "maxTokens": cfg.get("llm", {}).get("max_tokens", 2048),
        "systemPrompt": cfg.get("llm", {}).get("system_prompt", RECOMMENDED_PROMPT),
        "enforceCharLimit": bool(cfg.get("llm", {}).get("enforce_char_limit", False)),
        "searchEnabled": bool(web_search_cfg.get("enabled", True)),
        "searchProvider": web_search_cfg.get("default_provider", "duckduckgo"),
        "searxngUrl": env.get("SEARXNG_URL", web_search_cfg.get("searxng_url", "http://localhost:8888")),
        "dashboardEnabled": bool(dashboard_cfg.get("enabled", True)),
        "dashboardPort": dashboard_cfg.get("port", 5000),
        "screeningEnabled": bool(screening_cfg.get("enabled", False)),
        "screeningModel": screening_cfg.get("model", "gemini-2.5-flash"),
        "screeningAction": screening_cfg.get("action", "block"),
        "screeningPolicy": screening_cfg.get(
            "policy",
            "Keep responses safe, respectful, and appropriate for all audiences. "
            "Block content that is harmful, hateful, explicit, or violates Discord TOS.",
        ),
        "screeningChannelId": screening_cfg.get("channel_id", ""),
    }

    data["apiKeysSet"] = {
        "gemini": bool(env.get("GEMINI_API_KEY") and not env.get("GEMINI_API_KEY").startswith("your_")),
        "openai": bool(env.get("OPENAI_API_KEY") and not env.get("OPENAI_API_KEY").startswith("your_")),
        "anthropic": bool(env.get("ANTHROPIC_API_KEY") and not env.get("ANTHROPIC_API_KEY").startswith("your_")),
        "openrouter": bool(env.get("OPENROUTER_API_KEY") and not env.get("OPENROUTER_API_KEY").startswith("your_")),
    }

    return data


def _validate_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Perform basic validation on incoming setup payload."""
    required_keys = ["discord_token", "prefix", "provider", "model", "system_prompt"]
    missing = [k for k in required_keys if not str(payload.get(k, "")).strip()]
    if missing:
        return f"Missing required field(s): {', '.join(missing)}"

    provider = payload.get("provider")
    if provider not in PROVIDER_MODELS:
        return "Selected provider is not supported."

    if provider != "ollama" and not str(payload.get("api_key", "")).strip():
        return f"Please enter your {provider.title()} API key."

    dashboard_port = payload.get("dashboard_port")
    try:
        int(dashboard_port)
    except (TypeError, ValueError):
        return "Dashboard port must be a number."

    max_tokens = payload.get("max_tokens", "auto")
    if isinstance(max_tokens, str) and max_tokens.lower() != "auto":
        if not max_tokens.isdigit():
            return "Max tokens must be an integer or 'auto'."

    if payload.get("search_enabled") and payload.get("search_provider") == "searxng":
        url = str(payload.get("searxng_url", "")).strip()
        if not url:
            return "Please provide a SearxNG instance URL."

    if payload.get("screening_enabled"):
        if not str(payload.get("screening_policy", "")).strip():
            return "Please provide a screening policy."
        if payload.get("screening_action") == "escalate":
            channel_id = str(payload.get("screening_channel_id", "")).strip()
            if not channel_id.isdigit():
                return "Moderation channel ID must be a numeric Discord channel ID."

    return None


def _persist_configuration(payload: Dict[str, Any], config: ConfigManager, env_path: Path) -> None:
    """Persist configuration selections to YAML and .env."""
    logger.info("Saving configuration via web setup wizard")

    _set_env_value(env_path, "DISCORD_TOKEN", payload["discord_token"].strip())
    _set_env_value(env_path, "DISCORD_PREFIX", payload["prefix"].strip())

    provider = payload["provider"]
    model = payload.get("model") or PROVIDER_MODELS.get(provider, ["default"])[0]
    api_key = payload.get("api_key", "").strip()

    if provider == "gemini":
        _set_env_value(env_path, "GEMINI_API_KEY", api_key)
        _set_env_value(env_path, "DEFAULT_LLM_PROVIDER", "gemini")
        _set_env_value(env_path, "DEFAULT_MODEL", model)
    elif provider == "openai":
        _set_env_value(env_path, "OPENAI_API_KEY", api_key)
        _set_env_value(env_path, "DEFAULT_LLM_PROVIDER", "openai")
        _set_env_value(env_path, "DEFAULT_MODEL", model)
    elif provider == "anthropic":
        _set_env_value(env_path, "ANTHROPIC_API_KEY", api_key)
        _set_env_value(env_path, "DEFAULT_LLM_PROVIDER", "anthropic")
        _set_env_value(env_path, "DEFAULT_MODEL", model)
    elif provider == "ollama":
        _set_env_value(env_path, "DEFAULT_LLM_PROVIDER", "ollama")
        _set_env_value(env_path, "DEFAULT_MODEL", model)
    elif provider == "openrouter":
        _set_env_value(env_path, "OPENROUTER_API_KEY", api_key)
        _set_env_value(env_path, "DEFAULT_LLM_PROVIDER", "openrouter")
        _set_env_value(env_path, "DEFAULT_MODEL", model)

    config.set("bot.prefix", payload["prefix"].strip())
    config.set("llm.default_provider", provider)
    config.set("llm.default_model", model)
    config.set("llm.system_prompt", payload["system_prompt"].strip())

    temperature = float(payload.get("temperature", 0.7))
    config.set("llm.temperature", temperature)

    max_tokens = payload.get("max_tokens", "auto")
    if isinstance(max_tokens, str) and max_tokens.lower() == "auto":
        config.set("llm.max_tokens", "auto")
    else:
        config.set("llm.max_tokens", int(max_tokens))

    config.set("llm.enforce_char_limit", bool(payload.get("enforce_char_limit", False)))

    # Tools / web search
    search_enabled = bool(payload.get("search_enabled", True))
    config.set("tools.web_search.enabled", search_enabled)
    if search_enabled:
        provider_choice = payload.get("search_provider", "duckduckgo")
        config.set("tools.web_search.default_provider", provider_choice)
        if provider_choice == "searxng":
            searxng_url = payload.get("searxng_url", "http://localhost:8888").strip()
            config.set("tools.web_search.searxng_url", searxng_url)
            _set_env_value(env_path, "SEARXNG_URL", searxng_url)

    # Dashboard
    config.set("dashboard.enabled", bool(payload.get("dashboard_enabled", True)))
    config.set("dashboard.port", int(payload.get("dashboard_port", 5000)))

    # Screening
    screening_enabled = bool(payload.get("screening_enabled", False))
    config.set("screening.enabled", screening_enabled)
    if screening_enabled:
        config.set("screening.model", payload.get("screening_model", model))
        config.set("screening.action", payload.get("screening_action", "block"))
        config.set("screening.policy", payload.get("screening_policy"))
        if payload.get("screening_action") == "escalate":
            config.set("screening.channel_id", payload.get("screening_channel_id", ""))
        else:
            config.set("screening.channel_id", "")
    else:
        config.set("screening.model", None)
        config.set("screening.action", "block")
        config.set("screening.policy", None)
        config.set("screening.channel_id", "")


def create_setup_app(options: SetupOptions) -> Flask:
    """Create a standalone Flask app for the setup workflow."""
    env_path = _ensure_env_file()
    config_manager = ConfigManager()

    app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
    app.config["SETUP_OPTIONS"] = options
    app.config["ENV_PATH"] = env_path
    app.config["CONFIG_MANAGER"] = config_manager

    @app.route("/setup")
    def render_setup() -> str:
        return render_template("setup.html")

    @app.route("/api/setup/state")
    def setup_state():
        options: SetupOptions = app.config["SETUP_OPTIONS"]
        config_state = _serialize_config(config_manager)
        return jsonify(
            {
                "success": True,
                "data": config_state,
                "providers": [
                    {
                        "id": "gemini",
                        "name": "Google Gemini",
                        "tagline": "Fast, affordable, generous free tier",
                        "recommended": True,
                    },
                    {
                        "id": "openai",
                        "name": "OpenAI",
                        "tagline": "GPT-4 & GPT-3.5 family",
                        "recommended": False,
                    },
                    {
                        "id": "anthropic",
                        "name": "Anthropic",
                        "tagline": "Claude 3 family",
                        "recommended": False,
                    },
                    {
                        "id": "ollama",
                        "name": "Ollama (Local)",
                        "tagline": "Run local models for free",
                        "recommended": False,
                    },
                    {
                        "id": "openrouter",
                        "name": "OpenRouter",
                        "tagline": "Unified access to many providers",
                        "recommended": False,
                    },
                ],
                "models": PROVIDER_MODELS,
                "ollamaGuide": OLLAMA_GUIDE,
                "allowLaunch": options.allow_launch,
                "autoStartDashboard": options.auto_start_dashboard,
            }
        )

    @app.route("/api/setup/save", methods=["POST"])
    def save_setup():
        payload = request.get_json(force=True, silent=True) or {}
        error = _validate_payload(payload)
        if error:
            return jsonify({"success": False, "error": error}), 400

        try:
            _persist_configuration(payload, config_manager, env_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to persist setup configuration", exc_info=True)
            return jsonify({"success": False, "error": str(exc)}), 500

        options: SetupOptions = app.config["SETUP_OPTIONS"]
        if options.completion_event:
            options.completion_event.set()

        return jsonify({"success": True, "autoStart": options.auto_start_dashboard, "allowLaunch": options.allow_launch})

    @app.route("/api/setup/open-dashboard", methods=["POST"])
    def open_dashboard():
        options: SetupOptions = app.config["SETUP_OPTIONS"]
        if not options.allow_launch:
            return jsonify({"success": False, "error": "Dashboard launch is disabled in this mode."}), 400

        try:
            subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(ROOT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return jsonify({"success": True})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to launch main bot process", exc_info=True)
            return jsonify({"success": False, "error": str(exc)}), 500

    @app.route("/api/setup/generate-prompt", methods=["POST"])
    def generate_prompt():
        payload = request.get_json(force=True, silent=True) or {}
        user_request = payload.get("user_request", "").strip()
        
        if not user_request:
            return jsonify({"success": False, "error": "Please describe what you want your bot to do."}), 400

        provider = payload.get("provider")
        api_key = payload.get("api_key", "").strip()
        model = payload.get("model", "").strip()

        if not provider or not model:
            return jsonify({"success": False, "error": "Provider and model are required."}), 400

        if provider != "ollama" and not api_key:
            return jsonify({"success": False, "error": f"Please provide your {provider.title()} API key."}), 400

        try:
            # Create LLM provider instance
            llm = LLMProviderFactory.create_provider(provider, api_key=api_key)
            
            # Generate the prompt
            assistant_prompt = f"""You are a helpful assistant that creates system prompts for Discord bots.
The user wants their bot to: {user_request}

Create a clear, concise system prompt (2-4 sentences) that defines the bot's personality, tone, and behavior.
The prompt should be professional and suitable for a Discord bot.

Respond with ONLY the system prompt text, nothing else."""
            
            async def generate():
                response = await llm.complete(
                    messages=[Message(role="user", content=assistant_prompt)],
                    model=model,
                    max_tokens=300,
                    temperature=0.7
                )
                return response.content.strip()
            
            # Run async generation
            generated_prompt = asyncio.run(generate())
            
            return jsonify({"success": True, "prompt": generated_prompt})
            
        except Exception as exc:
            logger.error("Failed to generate prompt", exc_info=True)
            return jsonify({"success": False, "error": f"Could not generate prompt: {str(exc)}"}), 500

    return app


class _ServerThread(threading.Thread):
    """Utility thread for running Flask via werkzeug's make_server."""

    def __init__(self, app: Flask, host: str, port: int):
        super().__init__(daemon=True)
        self._server = make_server(host, port, app)
        self._ctx = app.app_context()
        self._ctx.push()

    def run(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._ctx.pop()


def run_web_setup(
    host: str = "127.0.0.1",
    port: int = 5050,
    *,
    open_browser: bool = True,
    auto_start_dashboard: bool = False,
    allow_launch: bool = False,
) -> None:
    """Run the setup server and block until the setup completes."""
    completion_event = threading.Event()
    options = SetupOptions(
        allow_launch=allow_launch,
        auto_start_dashboard=auto_start_dashboard,
        completion_event=completion_event,
    )
    app = create_setup_app(options)

    server = _ServerThread(app, host, port)
    server.start()

    url = f"http://{host}:{port}/setup"
    logger.info("Setup wizard available at %s", url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # pragma: no cover
            logger.warning("Unable to automatically open browser. Please visit %s manually.", url)

    completion_event.wait()
    server.shutdown()


def run_standalone_setup(
    host: str = "127.0.0.1",
    port: int = 5050,
    *,
    open_browser: bool = True,
    allow_launch: bool = True,
) -> None:
    """Run the setup server in standalone mode (non-blocking)."""
    options = SetupOptions(allow_launch=allow_launch, auto_start_dashboard=True, completion_event=None)
    app = create_setup_app(options)

    url = f"http://{host}:{port}/setup"
    logger.info("Launching setup wizard at %s", url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # pragma: no cover
            logger.warning("Unable to automatically open browser. Please visit %s manually.", url)

    app.run(host=host, port=port, debug=False, use_reloader=False)


def main_cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="OpenLLM Web Setup Wizard")
    parser.add_argument("--standalone", action="store_true", help="Run as a standalone setup server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5050, type=int)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.standalone:
        run_standalone_setup(
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
            allow_launch=True,
        )
    else:
        run_web_setup(
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
            auto_start_dashboard=False,
            allow_launch=False,
        )


if __name__ == "__main__":
    main_cli()
