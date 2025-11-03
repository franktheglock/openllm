"""
GUI Setup Wizard using customtkinter.
Modern, user-friendly interface for first-time configuration.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from pathlib import Path
from dotenv import set_key
import asyncio

from src.config.manager import ConfigManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SetupWizardGUI(ctk.CTk):
    """GUI Setup Wizard for OpenLLM."""

    def __init__(self):
        super().__init__()

        self.title("OpenLLM - Setup Wizard")
        self.geometry("900x940")
        self.minsize(850, 850)  # Set minimum size to prevent cutoff

        self.config_manager = ConfigManager()
        self.env_file = Path(".env")

        # Create .env if it doesn't exist
        if not self.env_file.exists():
            if Path(".env.example").exists():
                import shutil

                shutil.copy(".env.example", ".env")
            else:
                self.env_file.touch()

        # Current step
        self.current_step = 0
        self.total_steps = 6

        # Data storage
        self.setup_data = {
            "discord_token": tk.StringVar(),
            "prefix": tk.StringVar(value="!"),
            "llm_provider": tk.StringVar(value="gemini"),
            "llm_model": tk.StringVar(value="gemini-1.5-flash"),
            "api_key": tk.StringVar(),
            "model": tk.StringVar(),
            "temperature": tk.DoubleVar(value=0.7),
            "max_tokens": tk.StringVar(
                value="2048"
            ),  # Changed to StringVar to support 'auto'
            "system_prompt": tk.StringVar(
                value="You are a helpful Discord bot assistant. Be friendly, concise, and helpful."
            ),
            "enable_search": tk.BooleanVar(value=True),
            "search_provider": tk.StringVar(value="duckduckgo"),
            "searxng_url": tk.StringVar(value="http://localhost:8888"),
            "enable_dashboard": tk.BooleanVar(value=True),
            "dashboard_port": tk.IntVar(value=5000),
            "enable_screening": tk.BooleanVar(value=False),
            "screening_model": tk.StringVar(value="gemini-1.5-flash"),
            "screening_action": tk.StringVar(value="block"),
            "screening_policy": tk.StringVar(
                value="Keep responses safe, respectful, and appropriate for all audiences. Block content that is harmful, hateful, explicit, or violates Discord TOS."
            ),
            "screening_channel_id": tk.StringVar(value=""),
        }

        self.create_widgets()
        self.show_step(0)

    def create_widgets(self):
        """Create the main UI layout."""
        # Header
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0)
        self.header.pack(fill="x", padx=0, pady=0)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="🤖 OpenLLM Setup",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.title_label.pack(pady=20)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=700)
        self.progress.pack(pady=10)
        self.progress.set(0)

        # Step label
        self.step_label = ctk.CTkLabel(
            self, text="Step 1 of 4", font=ctk.CTkFont(size=14)
        )
        self.step_label.pack(pady=5)

        # Content frame (will hold different steps)
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.nav_frame.pack(fill="x", padx=0, pady=0)

        self.back_button = ctk.CTkButton(
            self.nav_frame, text="← Back", command=self.prev_step, width=120
        )
        self.back_button.pack(side="left", padx=20, pady=10)

        self.next_button = ctk.CTkButton(
            self.nav_frame, text="Next →", command=self.next_step, width=120
        )
        self.next_button.pack(side="right", padx=20, pady=10)

    def clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_step(self, step):
        """Show the specified step."""
        self.current_step = step
        self.progress.set((step + 1) / self.total_steps)
        self.step_label.configure(text=f"Step {step + 1} of {self.total_steps}")

        self.clear_content()

        if step == 0:
            self.show_discord_step()
        elif step == 1:
            self.show_llm_step()
        elif step == 2:
            self.show_system_prompt_step()
        elif step == 3:
            self.show_tools_step()
        elif step == 4:
            self.show_screening_step()
        elif step == 5:
            self.show_final_step()

        # Update button states
        self.back_button.configure(state="disabled" if step == 0 else "normal")
        if step == self.total_steps - 1:
            self.next_button.configure(text="Finish ✓")
        else:
            self.next_button.configure(text="Next →")

    def show_discord_step(self):
        """Step 1: Discord Configuration."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="Discord Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=20)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="First, let's set up your Discord bot connection.",
            font=ctk.CTkFont(size=12),
        )
        desc.pack(pady=5)

        # Discord token
        token_frame = ctk.CTkFrame(self.content_frame)
        token_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkLabel(
            token_frame,
            text="Discord Bot Token:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkEntry(
            token_frame,
            textvariable=self.setup_data["discord_token"],
            placeholder_text="Paste your Discord bot token here",
            width=500,
            show="•",
        ).pack(padx=10, pady=5)

        help_btn = ctk.CTkButton(
            token_frame,
            text="How to get a Discord token?",
            command=self.show_discord_help,
            fg_color="transparent",
            hover_color=("#3B8ED0", "#1F6AA5"),
        )
        help_btn.pack(pady=5)

        # Bot prefix
        prefix_frame = ctk.CTkFrame(self.content_frame)
        prefix_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            prefix_frame,
            text="Command Prefix:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkEntry(
            prefix_frame,
            textvariable=self.setup_data["prefix"],
            placeholder_text="!",
            width=100,
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            prefix_frame,
            text="Users will use this prefix for commands (e.g., !help)",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

    def show_llm_step(self):
        """Step 2: LLM Provider Configuration."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="AI Provider Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=20)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="Choose your AI provider and enter the API key.",
            font=ctk.CTkFont(size=12),
        )
        desc.pack(pady=5)

        # Provider selection
        provider_frame = ctk.CTkFrame(self.content_frame)
        provider_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkLabel(
            provider_frame,
            text="Select AI Provider:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        providers = [
            (
                "Google Gemini (Recommended - Fast & Affordable, very generous free tier)",
                "gemini",
            ),
            ("OpenAI (GPT-4, GPT-3.5)", "openai"),
            ("Anthropic (Claude 3)", "anthropic"),
            ("Ollama (Local, Free)", "ollama"),
            ("OpenRouter (Multiple Providers)", "openrouter"),
        ]

        for i, (label, value) in enumerate(providers):
            rb = ctk.CTkRadioButton(
                provider_frame,
                text=label,
                variable=self.setup_data["llm_provider"],
                value=value,
                command=self.on_provider_change,
            )
            rb.pack(anchor="w", padx=20, pady=5)
            if i == 0:  # First one is recommended
                rb.select()

        # API Key
        self.api_key_frame = ctk.CTkFrame(self.content_frame)
        self.api_key_frame.pack(fill="x", padx=40, pady=20)

        self.api_key_label = ctk.CTkLabel(
            self.api_key_frame,
            text="API Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.api_key_label.pack(anchor="w", padx=10, pady=5)

        self.api_key_entry = ctk.CTkEntry(
            self.api_key_frame,
            textvariable=self.setup_data["api_key"],
            placeholder_text="Enter your API key here",
            width=500,
            show="•",
        )
        self.api_key_entry.pack(padx=10, pady=5)

        self.api_help_btn = ctk.CTkButton(
            self.api_key_frame,
            text="How to get an API key?",
            command=self.show_api_help,
            fg_color="transparent",
            hover_color=("#3B8ED0", "#1F6AA5"),
        )
        self.api_help_btn.pack(pady=5)

        # Model selection
        self.model_frame = ctk.CTkFrame(self.content_frame)
        self.model_frame.pack(fill="x", padx=40, pady=20)

        self.model_label = ctk.CTkLabel(
            self.model_frame, text="Model:", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.model_label.pack(anchor="w", padx=10, pady=5)

        # Combobox for model selection (allows both selection and custom input)
        self.model_combo = ctk.CTkComboBox(
            self.model_frame,
            variable=self.setup_data["llm_model"],
            values=self.get_models_for_provider("gemini"),
            width=500,
        )
        self.model_combo.pack(padx=10, pady=5)

        self.on_provider_change()

    def get_models_for_provider(self, provider: str) -> list:
        """Get available models for a provider."""
        models = {
            "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
            "openai": ["gpt-5", "gpt-5-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ],
            "ollama": ["llama3.2", "llama3.1", "llama2", "mistral", "codellama"],
            "openrouter": ["Loading..."],  # Will be fetched from API
        }

        # Fetch OpenRouter models dynamically if that provider is selected
        if provider == "openrouter":
            try:
                import asyncio
                from src.llm.openrouter_provider import OpenRouterProvider

                # Try to fetch models if API key is available
                api_key = self.setup_data["api_key"].get()
                if api_key:
                    try:
                        openrouter = OpenRouterProvider(api_key=api_key)
                        # Run async function in sync context
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        fetched_models = loop.run_until_complete(
                            openrouter.fetch_models_from_api()
                        )
                        loop.close()
                        if fetched_models:
                            return fetched_models
                    except Exception as e:
                        logger.warning(f"Could not fetch OpenRouter models: {e}")

                # Return default list if fetch fails or no API key
                return [
                    "openai/gpt-4o",
                    "openai/gpt-4-turbo",
                    "anthropic/claude-3-5-sonnet-20241022",
                    "google/gemini-pro-1.5",
                    "meta-llama/llama-3.2-90b-vision-instruct",
                    "Type custom model name...",
                ]
            except Exception as e:
                logger.error(f"Error setting up OpenRouter models: {e}")
                return ["openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022"]

        return models.get(provider, ["default"])

    def show_system_prompt_step(self):
        """Step 3: System Prompt Configuration."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="System Prompt Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=15)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="Define how your bot should behave and respond to users.",
            font=ctk.CTkFont(size=12),
        )
        desc.pack(pady=5)

        # System prompt text area
        prompt_frame = ctk.CTkFrame(self.content_frame)
        prompt_frame.pack(fill="both", expand=True, padx=40, pady=15)

        ctk.CTkLabel(
            prompt_frame,
            text="System Prompt:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            prompt_frame,
            text="This defines the bot's personality, tone, and behavior guidelines.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        # Text area for system prompt
        self.system_prompt_text = ctk.CTkTextbox(
            prompt_frame, height=150, width=700, wrap="word"
        )
        self.system_prompt_text.pack(padx=10, pady=10)
        self.system_prompt_text.insert("1.0", self.setup_data["system_prompt"].get())

        # AI Assistant section
        assistant_frame = ctk.CTkFrame(self.content_frame)
        assistant_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            assistant_frame,
            text="💡 AI Prompt Assistant",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            assistant_frame,
            text="Describe what you want your bot to do, and AI will generate a system prompt for you.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        # Input for user request
        input_container = ctk.CTkFrame(assistant_frame)
        input_container.pack(fill="x", padx=10, pady=10)

        self.prompt_request_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="E.g., 'Make my bot act like a pirate who loves coding'",
            width=550,
        )
        self.prompt_request_entry.pack(side="left", padx=5)

        self.generate_prompt_btn = ctk.CTkButton(
            input_container,
            text="Generate Prompt",
            command=self.generate_system_prompt,
            width=130,
        )
        self.generate_prompt_btn.pack(side="left", padx=5)

        # Status label for generation
        self.prompt_status_label = ctk.CTkLabel(
            assistant_frame, text="", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.prompt_status_label.pack(anchor="w", padx=10, pady=2)

    def generate_system_prompt(self):
        """Generate a system prompt using AI."""
        user_request = self.prompt_request_entry.get()
        if not user_request.strip():
            messagebox.showwarning(
                "No Input", "Please describe what you want your bot to do."
            )
            return

        # Check if we have an API key configured
        provider = self.setup_data["llm_provider"].get()
        api_key = self.setup_data["api_key"].get()
        model = self.setup_data["llm_model"].get()

        if provider != "ollama" and not api_key:
            messagebox.showerror(
                "No API Key",
                f"Please configure your {provider.title()} API key in Step 2 before using the AI assistant.",
            )
            return

        self.prompt_status_label.configure(text="🤖 Generating prompt...")
        self.generate_prompt_btn.configure(state="disabled")
        self.update()

        # Run the async generation in a separate thread to avoid blocking the GUI
        import threading

        def run_generation():
            try:
                # Import the provider
                from src.llm.factory import LLMProviderFactory
                import asyncio
                from src.llm.base import Message

                # Create provider instance
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
                        temperature=0.7,
                    )
                    return response.content.strip()

                # Run the async function in a new event loop
                generated_prompt = asyncio.run(generate())

                # Update GUI from the main thread using after()
                self.after(0, self._update_generated_prompt, generated_prompt, None)

            except Exception as e:
                logger.error(f"Failed to generate prompt: {e}", exc_info=True)
                # Update GUI from the main thread using after()
                self.after(0, self._update_generated_prompt, None, str(e))

        # Start the generation in a background thread
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

    def _update_generated_prompt(self, generated_prompt, error):
        """Update the GUI with the generated prompt (called from main thread)."""
        try:
            if error:
                messagebox.showerror(
                    "Generation Failed", f"Could not generate prompt: {error}"
                )
                self.prompt_status_label.configure(
                    text="✗ Generation failed", text_color="red"
                )
            else:
                # Update the text area
                self.system_prompt_text.delete("1.0", "end")
                self.system_prompt_text.insert("1.0", generated_prompt)
                self.setup_data["system_prompt"].set(generated_prompt)
                self.prompt_status_label.configure(
                    text="✓ Prompt generated successfully!", text_color="green"
                )
        finally:
            self.generate_prompt_btn.configure(state="normal")

    def show_tools_step(self):
        """Step 4: Tools Configuration."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="Tools & Features",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=20)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="Enable additional features for your bot.",
            font=ctk.CTkFont(size=12),
        )
        desc.pack(pady=5)

        # Web Search
        search_frame = ctk.CTkFrame(self.content_frame)
        search_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkCheckBox(
            search_frame,
            text="Enable Web Search Tool",
            variable=self.setup_data["enable_search"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.on_search_toggle,
        ).pack(anchor="w", padx=10, pady=10)

        ctk.CTkLabel(
            search_frame,
            text="Allows the bot to search the internet for real-time information.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=30, pady=2)

        self.search_provider_frame = ctk.CTkFrame(search_frame)
        self.search_provider_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            self.search_provider_frame,
            text="Search Provider:",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=5)

        search_providers = [
            ("DuckDuckGo (Free, No API Key, pretty harsh rate limits)", "duckduckgo"),
            ("Google Custom Search", "google"),
            ("Brave Search", "brave"),
            ("SearxNG (Self-hosted, free, no rate limits)", "searxng"),
        ]

        for label, value in search_providers:
            ctk.CTkRadioButton(
                self.search_provider_frame,
                text=label,
                variable=self.setup_data["search_provider"],
                value=value,
                command=self.on_search_provider_change,
            ).pack(anchor="w", padx=10, pady=3)

        # SearxNG URL input (hidden by default)
        self.searxng_url_frame = ctk.CTkFrame(self.search_provider_frame)

        ctk.CTkLabel(
            self.searxng_url_frame,
            text="SearxNG Instance URL:",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=5)

        ctk.CTkEntry(
            self.searxng_url_frame,
            textvariable=self.setup_data["searxng_url"],
            placeholder_text="http://localhost:8888",
            width=400,
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            self.searxng_url_frame,
            text="Enter the URL of your SearxNG instance",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        # Dashboard
        dashboard_frame = ctk.CTkFrame(self.content_frame)
        dashboard_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkCheckBox(
            dashboard_frame,
            text="Enable Web Dashboard",
            variable=self.setup_data["enable_dashboard"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=10)

        ctk.CTkLabel(
            dashboard_frame,
            text="Web-based interface for monitoring and configuration.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=30, pady=2)

        port_frame = ctk.CTkFrame(dashboard_frame)
        port_frame.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(
            port_frame, text="Dashboard Port:", font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=5)

        ctk.CTkEntry(
            port_frame, textvariable=self.setup_data["dashboard_port"], width=100
        ).pack(side="left", padx=5)

        self.on_search_toggle()

    def show_screening_step(self):
        """Step 5: Content Screening Configuration."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="Content Screening (Optional)",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=15)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="Configure AI-powered content moderation to keep responses safe and appropriate.",
            font=ctk.CTkFont(size=12),
        )
        desc.pack(pady=5)

        # Enable screening checkbox
        enable_frame = ctk.CTkFrame(self.content_frame)
        enable_frame.pack(fill="x", padx=40, pady=15)

        ctk.CTkCheckBox(
            enable_frame,
            text="Enable Content Screening",
            variable=self.setup_data["enable_screening"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.on_screening_toggle,
        ).pack(anchor="w", padx=10, pady=10)

        ctk.CTkLabel(
            enable_frame,
            text="Uses AI to review bot responses before sending them to Discord.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=30, pady=2)

        # Screening configuration (shown when enabled)
        self.screening_config_frame = ctk.CTkFrame(self.content_frame)
        self.screening_config_frame.pack(fill="both", expand=True, padx=40, pady=10)

        # Model selection
        model_frame = ctk.CTkFrame(self.screening_config_frame)
        model_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            model_frame,
            text="Screening Model:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            model_frame,
            text="Choose a fast, cost-effective model for screening (e.g., gemini-flash, gpt-4o-mini).",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        # Use the same provider's models
        self.screening_model_combo = ctk.CTkComboBox(
            model_frame,
            variable=self.setup_data["screening_model"],
            values=self.get_models_for_provider(self.setup_data["llm_provider"].get()),
            width=500,
        )
        self.screening_model_combo.pack(padx=10, pady=5)

        # Action on flagged content
        action_frame = ctk.CTkFrame(self.screening_config_frame)
        action_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            action_frame,
            text="Action on Flagged Content:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        actions = [
            ("Block and notify user", "block"),
            ("Log but allow", "log"),
            ("Replace with safe message", "replace"),
            ("Escalate to moderators", "escalate"),
        ]

        for label, value in actions:
            ctk.CTkRadioButton(
                action_frame,
                text=label,
                variable=self.setup_data["screening_action"],
                value=value,
                command=self.on_screening_action_change,
            ).pack(anchor="w", padx=20, pady=3)

        # Moderation channel (shown only for escalate action)
        self.mod_channel_frame = ctk.CTkFrame(action_frame)
        self.mod_channel_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            self.mod_channel_frame,
            text="Moderation Channel ID:",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=10, pady=2)

        ctk.CTkEntry(
            self.mod_channel_frame,
            textvariable=self.setup_data["screening_channel_id"],
            placeholder_text="Right-click channel → Copy Channel ID",
            width=400,
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            self.mod_channel_frame,
            text="Flagged messages will be sent here for manual review.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        # Screening policy
        policy_frame = ctk.CTkFrame(self.screening_config_frame)
        policy_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            policy_frame,
            text="Screening Policy:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(
            policy_frame,
            text="Define what content should be flagged (e.g., harmful, inappropriate, offensive).",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=2)

        self.screening_policy_text = ctk.CTkTextbox(
            policy_frame, height=120, width=700, wrap="word"
        )
        self.screening_policy_text.pack(padx=10, pady=10)
        self.screening_policy_text.insert(
            "1.0", self.setup_data["screening_policy"].get()
        )

        self.on_screening_toggle()
        self.on_screening_action_change()  # Initialize channel visibility

    def on_screening_toggle(self):
        """Show/hide screening configuration based on checkbox."""
        if self.setup_data["enable_screening"].get():
            self.screening_config_frame.pack(fill="both", expand=True, padx=40, pady=10)
        else:
            self.screening_config_frame.pack_forget()

    def on_screening_action_change(self):
        """Show/hide moderation channel field based on action."""
        if self.setup_data["screening_action"].get() == "escalate":
            self.mod_channel_frame.pack(fill="x", padx=20, pady=10)
        else:
            self.mod_channel_frame.pack_forget()

    def show_final_step(self):
        """Step 6: Summary and finish."""
        title = ctk.CTkLabel(
            self.content_frame,
            text="Setup Complete! 🎉",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=30)

        desc = ctk.CTkLabel(
            self.content_frame,
            text="Review your configuration below:",
            font=ctk.CTkFont(size=14),
        )
        desc.pack(pady=10)

        # Summary frame
        summary_frame = ctk.CTkScrollableFrame(
            self.content_frame, width=600, height=300
        )
        summary_frame.pack(padx=40, pady=20)

        summary_items = [
            ("Discord Bot", "Configured ✓"),
            ("Command Prefix", self.setup_data["prefix"].get()),
            ("AI Provider", self.setup_data["llm_provider"].get().title()),
            ("AI Model", self.setup_data["llm_model"].get()),
            ("System Prompt", "Configured ✓"),
            (
                "Web Search",
                "Enabled" if self.setup_data["enable_search"].get() else "Disabled",
            ),
            (
                "Content Screening",
                "Enabled" if self.setup_data["enable_screening"].get() else "Disabled",
            ),
            (
                "Dashboard",
                (
                    f"Enabled (port {self.setup_data['dashboard_port'].get()})"
                    if self.setup_data["enable_dashboard"].get()
                    else "Disabled"
                ),
            ),
        ]

        for key, value in summary_items:
            item_frame = ctk.CTkFrame(summary_frame)
            item_frame.pack(fill="x", pady=5, padx=10)

            ctk.CTkLabel(
                item_frame,
                text=key + ":",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=150,
                anchor="w",
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                item_frame, text=value, font=ctk.CTkFont(size=13), anchor="w"
            ).pack(side="left", padx=10)

        info = ctk.CTkLabel(
            self.content_frame,
            text="Click 'Finish' to save your configuration and start using the bot!",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        info.pack(pady=20)

    def on_provider_change(self):
        """Handle provider selection change."""
        provider = self.setup_data["llm_provider"].get()

        if provider == "ollama":
            self.api_key_frame.pack_forget()
        else:
            self.api_key_frame.pack(fill="x", padx=40, pady=20)

            # Update placeholder
            provider_names = {
                "gemini": "Gemini",
                "openai": "OpenAI",
                "anthropic": "Anthropic",
                "openrouter": "OpenRouter",
            }
            name = provider_names.get(provider, provider.title())
            self.api_key_entry.configure(placeholder_text=f"Enter your {name} API key")

        # Update model dropdown
        if hasattr(self, "model_combo"):
            models = self.get_models_for_provider(provider)
            self.model_combo.configure(values=models)
            if models:
                self.setup_data["llm_model"].set(models[0])  # Set first as default

    def on_search_toggle(self):
        """Handle search toggle."""
        if self.setup_data["enable_search"].get():
            self.search_provider_frame.pack(fill="x", padx=30, pady=10)
            self.on_search_provider_change()  # Check if SearxNG is selected
        else:
            self.search_provider_frame.pack_forget()
            self.searxng_url_frame.pack_forget()

    def on_search_provider_change(self):
        """Handle search provider change."""
        if self.setup_data["search_provider"].get() == "searxng":
            self.searxng_url_frame.pack(fill="x", padx=10, pady=10)
        else:
            self.searxng_url_frame.pack_forget()

    def show_discord_help(self):
        """Show help for getting Discord token."""
        help_text = """To get your Discord bot token:

1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name
3. Go to the "Bot" tab on the left
4. Click "Add Bot"
5. Under "Token", click "Reset Token" and copy it
6. Enable these Privileged Gateway Intents:
   ✓ MESSAGE CONTENT INTENT
   ✓ SERVER MEMBERS INTENT
7. Go to OAuth2 > URL Generator
8. Select scopes: bot, applications.commands
9. Select bot permissions:
   ✓ Read Messages/View Channels
   ✓ Send Messages
   ✓ Read Message History
10. Copy the generated URL and invite bot to your server

Paste your token in the field above."""

        messagebox.showinfo("Getting Discord Token", help_text)

    def show_api_help(self):
        """Show help for getting API key."""
        provider = self.setup_data["llm_provider"].get()

        help_texts = {
            "gemini": """To get a Gemini API key:

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API key"
4. Copy your API key

Gemini offers generous free tier:
• 60 requests per minute
• 1,500 requests per day
• Perfect for getting started!""",
            "openai": """To get an OpenAI API key:

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section
4. Click "Create new secret key"
5. Copy and save your key

Note: Requires payment method for usage.""",
            "anthropic": """To get an Anthropic API key:

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys
4. Click "Create Key"
5. Copy and save your key""",
            "openrouter": """To get an OpenRouter API key:

1. Go to https://openrouter.ai/
2. Sign up with GitHub or email
3. Go to Keys section
4. Create a new API key
5. Copy and save your key""",
        }

        help_text = help_texts.get(
            provider, "Please visit the provider's website for API key instructions."
        )
        messagebox.showinfo(f"Getting {provider.title()} API Key", help_text)

    def next_step(self):
        """Go to next step or finish."""
        # Validate current step
        if not self.validate_current_step():
            return

        if self.current_step < self.total_steps - 1:
            self.show_step(self.current_step + 1)
        else:
            self.finish_setup()

    def prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def validate_current_step(self):
        """Validate current step data."""
        if self.current_step == 0:
            if not self.setup_data["discord_token"].get():
                messagebox.showerror("Error", "Please enter your Discord bot token.")
                return False

        elif self.current_step == 1:
            provider = self.setup_data["llm_provider"].get()
            if provider != "ollama" and not self.setup_data["api_key"].get():
                messagebox.showerror(
                    "Error", f"Please enter your {provider.title()} API key."
                )
                return False

        elif self.current_step == 2:
            # Save system prompt from text area
            prompt = self.system_prompt_text.get("1.0", "end-1c").strip()
            if not prompt:
                messagebox.showerror("Error", "Please enter a system prompt.")
                return False
            self.setup_data["system_prompt"].set(prompt)

        elif self.current_step == 4:
            # Save screening policy from text area if screening is enabled
            if self.setup_data["enable_screening"].get():
                policy = self.screening_policy_text.get("1.0", "end-1c").strip()
                if not policy:
                    messagebox.showerror("Error", "Please enter a screening policy.")
                    return False
                self.setup_data["screening_policy"].set(policy)

                # Validate channel ID if escalate action is selected
                if self.setup_data["screening_action"].get() == "escalate":
                    channel_id = self.setup_data["screening_channel_id"].get().strip()
                    if not channel_id:
                        messagebox.showerror(
                            "Error",
                            "Please enter a moderation channel ID for escalation.",
                        )
                        return False
                    if not channel_id.isdigit():
                        messagebox.showerror("Error", "Channel ID must be a number.")
                        return False

        return True

    def finish_setup(self):
        """Save configuration and finish setup."""
        try:
            # Save to .env
            self._set_env("DISCORD_TOKEN", self.setup_data["discord_token"].get())
            self._set_env("DISCORD_PREFIX", self.setup_data["prefix"].get())

            provider = self.setup_data["llm_provider"].get()
            model = self.setup_data["llm_model"].get()

            if provider == "gemini":
                self._set_env("GEMINI_API_KEY", self.setup_data["api_key"].get())
                self._set_env("DEFAULT_LLM_PROVIDER", "gemini")
                self._set_env("DEFAULT_MODEL", model or "gemini-1.5-flash")
            elif provider == "openai":
                self._set_env("OPENAI_API_KEY", self.setup_data["api_key"].get())
                self._set_env("DEFAULT_LLM_PROVIDER", "openai")
                self._set_env("DEFAULT_MODEL", model or "gpt-4o")
            elif provider == "anthropic":
                self._set_env("ANTHROPIC_API_KEY", self.setup_data["api_key"].get())
                self._set_env("DEFAULT_LLM_PROVIDER", "anthropic")
                self._set_env("DEFAULT_MODEL", model or "claude-3-5-sonnet-20241022")
            elif provider == "ollama":
                self._set_env("DEFAULT_LLM_PROVIDER", "ollama")
                self._set_env("DEFAULT_MODEL", model or "llama3.2")
            elif provider == "openrouter":
                self._set_env("OPENROUTER_API_KEY", self.setup_data["api_key"].get())
                self._set_env("DEFAULT_LLM_PROVIDER", "openrouter")
                self._set_env("DEFAULT_MODEL", model or "openai/gpt-4o")

            # Save to config.yaml
            self.config_manager.set("bot.prefix", self.setup_data["prefix"].get())
            self.config_manager.set("llm.default_provider", provider)
            self.config_manager.set("llm.default_model", model)
            self.config_manager.set(
                "llm.temperature", self.setup_data["temperature"].get()
            )
            self.config_manager.set(
                "llm.max_tokens", self.setup_data["max_tokens"].get()
            )
            self.config_manager.set(
                "llm.system_prompt", self.setup_data["system_prompt"].get()
            )

            self.config_manager.set(
                "tools.web_search.enabled", self.setup_data["enable_search"].get()
            )
            if self.setup_data["enable_search"].get():
                self.config_manager.set(
                    "tools.web_search.default_provider",
                    self.setup_data["search_provider"].get(),
                )
                # Save SearxNG URL if that provider is selected
                if self.setup_data["search_provider"].get() == "searxng":
                    searxng_url = self.setup_data["searxng_url"].get()
                    self.config_manager.set("tools.web_search.searxng_url", searxng_url)
                    self._set_env("SEARXNG_URL", searxng_url)

            self.config_manager.set(
                "dashboard.enabled", self.setup_data["enable_dashboard"].get()
            )
            self.config_manager.set(
                "dashboard.port", self.setup_data["dashboard_port"].get()
            )

            # Save screening configuration
            self.config_manager.set(
                "screening.enabled", self.setup_data["enable_screening"].get()
            )
            if self.setup_data["enable_screening"].get():
                self.config_manager.set(
                    "screening.model", self.setup_data["screening_model"].get()
                )
                self.config_manager.set(
                    "screening.action", self.setup_data["screening_action"].get()
                )
                self.config_manager.set(
                    "screening.policy", self.setup_data["screening_policy"].get()
                )
                if self.setup_data["screening_action"].get() == "escalate":
                    self.config_manager.set(
                        "screening.channel_id",
                        self.setup_data["screening_channel_id"].get(),
                    )

            messagebox.showinfo(
                "Setup Complete!",
                "Configuration saved successfully!\n\n"
                "You can now start the bot.\n"
                "The setup wizard will close.",
            )

            self.destroy()  # Close the window properly

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            logger.error(f"Setup error: {e}", exc_info=True)

    def _set_env(self, key: str, value: str):
        """Set environment variable in .env file."""
        set_key(str(self.env_file), key, str(value))
        os.environ[key] = str(value)


def run_gui_setup():
    """Run the GUI setup wizard."""
    app = SetupWizardGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui_setup()
