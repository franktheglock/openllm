"""
Setup wizard for first-time configuration.
"""
import os
import asyncio
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from dotenv import set_key

from src.config.manager import ConfigManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
console = Console()


class SetupWizard:
    """Interactive setup wizard for bot configuration."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.config_manager = ConfigManager()
        self.env_file = Path('.env')
        
        # Create .env if it doesn't exist
        if not self.env_file.exists():
            if Path('.env.example').exists():
                import shutil
                shutil.copy('.env.example', '.env')
            else:
                self.env_file.touch()
    
    async def run(self):
        """Run the setup wizard."""
        console.print(Panel.fit(
            "[bold cyan]Discord LLM Bot Setup Wizard[/bold cyan]\n"
            "Welcome! Let's configure your bot.",
            border_style="cyan"
        ))
        
        # Step 1: Discord Configuration
        await self._setup_discord()
        
        # Step 2: LLM Provider
        await self._setup_llm_provider()
        
        # Step 3: Tools
        await self._setup_tools()
        
        # Step 4: Optional Features
        await self._setup_optional_features()
        
        # Summary
        console.print("\n[bold green]✓ Setup complete![/bold green]")
        console.print("\nYou can now start the bot with: [cyan]python main.py[/cyan]")
        console.print("Access the dashboard at: [cyan]http://localhost:5000[/cyan]\n")
    
    async def _setup_discord(self):
        """Setup Discord bot configuration."""
        console.print("\n[bold]Step 1: Discord Configuration[/bold]")
        
        token = Prompt.ask(
            "Enter your Discord Bot Token",
            default=os.getenv('DISCORD_TOKEN', '')
        )
        self._set_env('DISCORD_TOKEN', token)
        
        prefix = Prompt.ask(
            "Command prefix",
            default=self.config_manager.get('bot.prefix', '!')
        )
        self.config_manager.set('bot.prefix', prefix)
        
        console.print("[green]✓ Discord configured[/green]")
    
    async def _setup_llm_provider(self):
        """Setup LLM provider."""
        console.print("\n[bold]Step 2: LLM Provider Setup[/bold]")
        
        # Show available providers
        table = Table(title="Available LLM Providers")
        table.add_column("Number", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("Models", style="yellow")
        
        providers_info = [
            ("1", "OpenAI", "GPT-4, GPT-3.5"),
            ("2", "Anthropic", "Claude 3 (Opus, Sonnet, Haiku)"),
            ("3", "OpenRouter", "Multiple models"),
            ("4", "Ollama", "Local models (Llama2, Mistral, etc.)")
        ]
        
        for num, name, models in providers_info:
            table.add_row(num, name, models)
        
        console.print(table)
        
        choice = Prompt.ask(
            "Select your LLM provider",
            choices=["1", "2", "3", "4"],
            default="1"
        )
        
        provider_map = {
            "1": ("openai", "OPENAI_API_KEY", "gpt-4-turbo-preview"),
            "2": ("anthropic", "ANTHROPIC_API_KEY", "claude-3-sonnet-20240229"),
            "3": ("openrouter", "OPENROUTER_API_KEY", "openai/gpt-4-turbo-preview"),
            "4": ("ollama", None, "llama2")
        }
        
        provider_name, env_key, default_model = provider_map[choice]
        
        if env_key:
            api_key = Prompt.ask(
                f"Enter your {provider_name.title()} API Key",
                password=True
            )
            self._set_env(env_key, api_key)
        
        self.config_manager.set('llm.default_provider', provider_name)
        self.config_manager.set('llm.default_model', default_model)
        
        # LLM parameters
        temperature = Prompt.ask(
            "Temperature (0.0-2.0, higher = more creative)",
            default=str(self.config_manager.get('llm.temperature', 0.7))
        )
        self.config_manager.set('llm.temperature', float(temperature))
        
        max_tokens = Prompt.ask(
            "Max tokens per response",
            default=str(self.config_manager.get('llm.max_tokens', 2048))
        )
        self.config_manager.set('llm.max_tokens', int(max_tokens))
        
        console.print(f"[green]✓ {provider_name.title()} configured[/green]")
    
    async def _setup_tools(self):
        """Setup tools configuration."""
        console.print("\n[bold]Step 3: Tools Configuration[/bold]")
        
        # Web Search
        enable_search = Confirm.ask(
            "Enable web search tool?",
            default=True
        )
        
        if enable_search:
            table = Table(title="Search Providers")
            table.add_column("Number", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Requirements", style="yellow")
            
            search_providers = [
                ("1", "DuckDuckGo", "None (free)"),
                ("2", "Google", "API Key + CSE ID"),
                ("3", "Brave", "API Key"),
                ("4", "SearxNG", "Self-hosted instance")
            ]
            
            for num, name, req in search_providers:
                table.add_row(num, name, req)
            
            console.print(table)
            
            search_choice = Prompt.ask(
                "Select search provider",
                choices=["1", "2", "3", "4"],
                default="1"
            )
            
            search_map = {
                "1": "duckduckgo",
                "2": "google",
                "3": "brave",
                "4": "searxng"
            }
            
            provider = search_map[search_choice]
            self.config_manager.set('tools.web_search.enabled', True)
            self.config_manager.set('tools.web_search.default_provider', provider)
            
            # Configure provider-specific settings
            if provider == "google":
                api_key = Prompt.ask("Google API Key", password=True)
                cse_id = Prompt.ask("Google Custom Search Engine ID")
                self._set_env('GOOGLE_API_KEY', api_key)
                self._set_env('GOOGLE_CSE_ID', cse_id)
            
            elif provider == "brave":
                api_key = Prompt.ask("Brave API Key", password=True)
                self._set_env('BRAVE_API_KEY', api_key)
            
            elif provider == "searxng":
                url = Prompt.ask("SearxNG Instance URL", default="http://localhost:8080")
                self._set_env('SEARXNG_URL', url)
            
            console.print(f"[green]✓ Web search configured ({provider})[/green]")
        else:
            self.config_manager.set('tools.web_search.enabled', False)
    
    async def _setup_optional_features(self):
        """Setup optional features."""
        console.print("\n[bold]Step 4: Optional Features[/bold]")
        
        # Dashboard
        enable_dashboard = Confirm.ask(
            "Enable web dashboard?",
            default=True
        )
        self.config_manager.set('dashboard.enabled', enable_dashboard)
        
        if enable_dashboard:
            port = Prompt.ask(
                "Dashboard port",
                default=str(self.config_manager.get('dashboard.port', 5000))
            )
            self.config_manager.set('dashboard.port', int(port))
        
        # Content moderation
        enable_moderation = Confirm.ask(
            "Enable content moderation?",
            default=False
        )
        self.config_manager.set('moderation.enabled', enable_moderation)
        
        # Plugin system
        enable_plugins = Confirm.ask(
            "Enable plugin system?",
            default=True
        )
        self.config_manager.set('plugins.enabled', enable_plugins)
        
        console.print("[green]✓ Optional features configured[/green]")
    
    def _set_env(self, key: str, value: str):
        """Set environment variable in .env file."""
        set_key(str(self.env_file), key, value)
        os.environ[key] = value
