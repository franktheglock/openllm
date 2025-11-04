"""
Main Discord bot implementation.
"""
import discord
from discord.ext import commands
import os
import asyncio
from typing import Optional, Dict, List
from pathlib import Path

from src.config.manager import ConfigManager
from src.llm.factory import LLMProviderFactory
from src.llm.base import Message, BaseLLMProvider
from src.tools.base import BaseTool
from src.utils.logger import setup_logger
from src.utils.conversation_manager import ConversationManager

logger = setup_logger(__name__)


class DiscordLLMBot:
    """Main Discord bot class."""
    
    def __init__(self, config_path: str = "config.yaml", enable_dashboard: bool = True):
        """
        Initialize the Discord bot.
        
        Args:
            config_path: Path to configuration file
            enable_dashboard: Whether to enable the web dashboard
        """
        self.config_manager = ConfigManager(config_path)
        self.enable_dashboard = enable_dashboard
        
        # Setup Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        prefix = self.config_manager.get('bot.prefix', '!')
        self.bot = commands.Bot(command_prefix=prefix, intents=intents)
        
        # LLM providers cache
        self.llm_providers: Dict[str, BaseLLMProvider] = {}
        
        # Tools
        self.tools: Dict[str, BaseTool] = {}
        self._load_tools()
        
        # Conversation history (server_id -> channel_id -> messages)
        self.conversations: Dict[str, Dict[str, List[Message]]] = {}
        
        # Token-efficient conversation manager
        self.conversation_manager = ConversationManager(
            max_context_tokens=self.config_manager.get('llm.max_context_tokens', 32000),
            reserve_tokens=self.config_manager.get('llm.reserve_tokens', 2048),
            min_messages=self.config_manager.get('llm.min_messages', 2)
        )
        
        # Register event handlers
        self._register_events()
        
        logger.info("Discord LLM Bot initialized")
    
    def _load_tools(self):
        """Load enabled tools and plugins."""
        # Load plugins (including built-in web_search)
        import sqlite3
        from pathlib import Path
        import importlib.util
        import json
        
        plugins_dir = Path('plugins')
        if not plugins_dir.exists():
            logger.warning("Plugins directory not found")
            return
        
        # Get enabled plugins from database
        with sqlite3.connect(self.config_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, enabled FROM plugins")
            enabled_plugins = {row[0]: bool(row[1]) for row in cursor.fetchall()}
        
        logger.info(f"Found {len(enabled_plugins)} plugins in database: {list(enabled_plugins.keys())}")
        
        # Ensure built-in plugins are installed
        builtin_plugins = []
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / 'manifest.json'
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if not content:
                            logger.warning(f"Skipping plugin {plugin_dir.name}: Empty manifest.json")
                            continue
                        manifest = json.loads(content)
                        if manifest.get('builtin', False):
                            builtin_plugins.append((manifest.get('name'), manifest.get('version', '1.0.0')))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Skipping plugin {plugin_dir.name}: Invalid manifest.json - {e}")
                    continue
        
        # Install built-in plugins if not in database
        if builtin_plugins:
            with sqlite3.connect(self.config_manager.db_path) as conn:
                cursor = conn.cursor()
                for plugin_name, version in builtin_plugins:
                    cursor.execute("SELECT 1 FROM plugins WHERE name = ?", (plugin_name,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO plugins (name, version, enabled, config_json)
                            VALUES (?, ?, 1, '{}')
                        """, (plugin_name, version))
                        enabled_plugins[plugin_name] = True
                        logger.info(f"Auto-installed built-in plugin: {plugin_name}")
                conn.commit()
        
        # Load each plugin
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            manifest_path = plugin_dir / 'manifest.json'
            plugin_file = plugin_dir / 'plugin.py'
            
            if not manifest_path.exists() or not plugin_file.exists():
                continue
            
            try:
                # Load manifest
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        logger.warning(f"Skipping plugin {plugin_dir.name}: Empty manifest.json")
                        continue
                    manifest = json.loads(content)
                
                plugin_name = manifest.get('name')
                if not plugin_name:
                    logger.warning(f"Skipping plugin {plugin_dir.name}: No 'name' field in manifest")
                    continue
                
                # Check if plugin is enabled
                if plugin_name not in enabled_plugins or not enabled_plugins[plugin_name]:
                    logger.debug(f"Plugin '{plugin_name}' is not enabled, skipping")
                    continue
                
                # Load plugin module
                spec = importlib.util.spec_from_file_location(f"plugin_{plugin_dir.name}", plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Instantiate plugin
                    plugin = module.Plugin()
                    
                    # Register plugin tools
                    for tool in plugin.get_tools():
                        tool_def = tool.get_definition()
                        self.tools[tool_def.name] = tool
                        logger.info(f"Loaded tool '{tool_def.name}' from plugin '{plugin_name}'")
                
            except Exception as e:
                logger.error(f"Error loading plugin from {plugin_dir.name}: {e}", exc_info=True)
        
        # Log total tools loaded
        logger.info(f"Total tools loaded: {len(self.tools)} - {list(self.tools.keys())}")
    
    def _register_events(self):
        """Register Discord event handlers."""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.bot.user}')
            
            # Initialize server configs for all guilds
            for guild in self.bot.guilds:
                await self._ensure_server_config(str(guild.id))
            
            # Set status
            activity_text = self.config_manager.get('bot.activity', 'Chatting with AI')
            activity = discord.Game(name=activity_text)
            await self.bot.change_presence(activity=activity)
            
            # Start dashboard if enabled
            if self.enable_dashboard:
                asyncio.create_task(self._start_dashboard())
        
        @self.bot.event
        async def on_guild_join(guild: discord.Guild):
            """Called when bot joins a new guild."""
            logger.info(f'Joined guild: {guild.name} (ID: {guild.id})')
            await self._ensure_server_config(str(guild.id))
        
        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return
            
            # Check if bot is mentioned or message starts with prefix
            mentioned = self.bot.user in message.mentions
            prefix = self.config_manager.get('bot.prefix', '!')
            has_prefix = message.content.startswith(prefix)
            
            # Check if DMs are enabled
            is_dm = isinstance(message.channel, discord.DMChannel)
            dm_enabled = self.config_manager.get('bot.enable_dm', False)
            
            if mentioned or has_prefix or (is_dm and dm_enabled):
                await self._handle_llm_message(message)
            
            # Process commands
            await self.bot.process_commands(message)
    
    async def _handle_llm_message(self, message: discord.Message):
        """
        Handle a message that should be processed by the LLM.
        
        Args:
            message: Discord message
        """
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Get server configuration
                server_id = str(message.guild.id) if message.guild else "DM"
                server_config = self.config_manager.get_server_config(server_id)
                
                # Add server_id and user_id to config for tool call logging
                server_config['server_id'] = server_id
                server_config['user_id'] = str(message.author.id)
                
                # Clean message content
                content = message.content
                # Remove bot mention
                content = content.replace(f'<@{self.bot.user.id}>', '').strip()
                # Remove prefix if present
                prefix = self.config_manager.get('bot.prefix', '!')
                if content.startswith(prefix):
                    content = content[len(prefix):].strip()
                
                # Get or create conversation history
                if server_id not in self.conversations:
                    self.conversations[server_id] = {}
                if str(message.channel.id) not in self.conversations[server_id]:
                    self.conversations[server_id][str(message.channel.id)] = []
                
                conversation = self.conversations[server_id][str(message.channel.id)]
                
                # Add system prompt if this is the first message
                if not conversation:
                    system_prompt = self.config_manager.get('prompts.system', '')
                    
                    # Add character limit instruction if enabled
                    if server_config.get('enforce_char_limit', False):
                        char_limit_instruction = "\n\nIMPORTANT: Keep your responses under 2000 characters to ensure they fit in a single Discord message. Be concise and direct."
                        system_prompt = system_prompt + char_limit_instruction if system_prompt else char_limit_instruction.strip()
                    
                    if system_prompt:
                        conversation.append(Message(role='system', content=system_prompt))
                
                # Add user message and prune conversation to fit token limits
                conversation = self.conversation_manager.add_message(
                    conversation, 
                    Message(role='user', content=content),
                    server_config.get('llm_model')
                )
                
                # Get LLM provider
                provider = self._get_llm_provider(
                    server_config.get('llm_provider'),
                    server_id
                )
                
                # Get available tools - use all loaded tools
                tool_definitions = None
                if self.tools:
                    # If server has specific enabled_tools configured and it's not empty, use those
                    # Otherwise, use all loaded tools
                    enabled_tools = server_config.get('enabled_tools', [])
                    if enabled_tools:
                        tool_definitions = [
                            self.tools[tool_name].to_openai_tool()
                            for tool_name in enabled_tools
                            if tool_name in self.tools
                        ]
                        logger.debug(f"Using server-specific enabled_tools: {enabled_tools}")
                    else:
                        # Use all loaded tools
                        tool_definitions = [
                            tool.to_openai_tool()
                            for tool in self.tools.values()
                        ]
                        logger.debug(f"Using all loaded tools: {list(self.tools.keys())}")
                    
                    logger.info(f"Passing {len(tool_definitions) if tool_definitions else 0} tools to LLM")
                
                # Get completion
                response = await provider.complete(
                    messages=conversation,
                    model=server_config.get('llm_model'),
                    temperature=server_config.get('temperature', 0.7),
                    max_tokens=server_config.get('max_tokens', 2048),
                    tools=tool_definitions
                )
                
                # Handle tool calls
                if response.tool_calls:
                    response = await self._handle_tool_calls(
                        response,
                        conversation,
                        provider,
                        server_config,
                        tool_definitions  # Pass tool definitions to second call
                    )
                
                # Log response content for debugging
                logger.debug(f"Response content length: {len(response.content) if response.content else 0}")
                logger.debug(f"Response content: {response.content[:100] if response.content else 'None'}")
                
                # Add assistant response to conversation (with token management)
                conversation = self.conversation_manager.add_message(
                    conversation,
                    Message(role='assistant', content=response.content),
                    server_config.get('llm_model')
                )
                
                # Send response
                await self._send_response(message, response.content)
                
                # Log usage
                self._log_usage(server_id, str(message.author.id), server_config, response)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await message.reply("Sorry, I encountered an error processing your message.", mention_author=False)
    
    async def _handle_tool_calls(
        self,
        response,
        conversation: List[Message],
        provider: BaseLLMProvider,
        server_config: Dict,
        tool_definitions: Optional[List[Dict]] = None,
        depth: int = 0,
        max_depth: int = 5
    ):
        """Handle tool calls from LLM response."""
        server_id = str(server_config.get('server_id', 'DM'))
        user_id = str(server_config.get('user_id', 'unknown'))
        
        tool_definitions = tool_definitions or []

        if depth >= max_depth:
            logger.warning("Maximum tool call depth reached; returning last response")
            return response

        # Add assistant message with tool calls (with token management)
        conversation = self.conversation_manager.add_message(
            conversation,
            Message(
                role='assistant',
                content=response.content or "",
                tool_calls=response.tool_calls
            ),
            server_config.get('llm_model')
        )

        tool_results: List[tuple[str, str]] = []

        # Execute each tool call
        for tool_call in response.tool_calls:
            # Tool calls are now always in dict format (converted by providers)
            tool_name = tool_call['function']['name']
            tool_args_str = tool_call['function']['arguments']
            tool_call_id = tool_call['id']
            
            # Parse arguments
            import json
            try:
                tool_args = json.loads(tool_args_str)
            except:
                tool_args = eval(tool_args_str)  # Fallback to eval
            
            result = None
            success = False
            error_message = None
            
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name].execute(**tool_args)
                    success = True
                    tool_results.append((tool_name, str(result)))
                except Exception as e:
                    result = f"Error: {str(e)}"
                    error_message = str(e)
                    logger.error(f"Tool execution error: {e}", exc_info=True)
                    tool_results.append((tool_name, result))
                
                # Add tool result to conversation (with token management)
                conversation = self.conversation_manager.add_message(
                    conversation,
                    Message(
                        role='tool',
                        content=result,
                        tool_call_id=tool_call_id
                    ),
                    server_config.get('llm_model')
                )
            else:
                result = f"Tool {tool_name} not found"
                error_message = f"Tool {tool_name} not found"
                tool_results.append((tool_name, result))
            
            # Log tool call to database
            self._log_tool_call(
                server_id=server_id,
                user_id=user_id,
                tool_name=tool_name,
                parameters=json.dumps(tool_args),
                result=str(result)[:1000] if result else "",
                success=success,
                error_message=error_message
            )
        
        # Log conversation state before final call
        logger.info(f"Conversation before final call has {len(conversation)} messages")
        for i, msg in enumerate(conversation[-5:]):  # Log last 5 messages
            logger.debug(f"  Message {i}: role={msg.role}, content_len={len(msg.content) if msg.content else 0}, has_tool_calls={bool(msg.tool_calls)}, tool_call_id={msg.tool_call_id}")
        
        # Get final response with tool results
        final_response = await provider.complete(
            messages=conversation,
            model=server_config.get('llm_model'),
            temperature=server_config.get('temperature', 0.7),
            max_tokens=server_config.get('max_tokens', 2048),
            tools=tool_definitions  # Pass tools so LLM can interpret results
        )
        
        # Log the final response details
        logger.info(f"Final response after tools - content: {final_response.content[:200] if final_response.content else 'EMPTY'}")
        logger.info(f"Final response - finish_reason: {final_response.finish_reason}")
        logger.info(f"Final response - has tool_calls: {bool(final_response.tool_calls)}")
        
        if final_response.tool_calls:
            logger.info("LLM requested additional tool calls after follow-up response")
            return await self._handle_tool_calls(
                final_response,
                conversation,
                provider,
                server_config,
                tool_definitions,
                depth + 1,
                max_depth
            )
        
        # Ensure final response has content
        if not final_response.content or not final_response.content.strip():
            logger.warning("LLM returned empty response after tool execution; falling back to tool result summary")
            if tool_results:
                summary_lines = [f"{name}: {result}" for name, result in tool_results]
                final_response.content = "\n".join(summary_lines)
            else:
                final_response.content = "I've processed your request using the available tools."
        
        return final_response
    
    async def _ensure_server_config(self, server_id: str):
        """Ensure a server has a configuration entry in the database."""
        import sqlite3
        
        with sqlite3.connect(self.config_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT server_id FROM server_config WHERE server_id = ?", (server_id,))
            
            if not cursor.fetchone():
                # Create default config with all available tools
                tool_names = ','.join(self.tools.keys()) if self.tools else ''
                
                cursor.execute("""
                    INSERT INTO server_config 
                    (server_id, llm_provider, llm_model, temperature, max_tokens, enabled_tools)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    server_id,
                    self.config_manager.get('llm.default_provider'),
                    self.config_manager.get('llm.default_model'),
                    self.config_manager.get('llm.temperature', 0.7),
                    self.config_manager.get('llm.max_tokens', 2048),
                    tool_names
                ))
                conn.commit()
                logger.info(f"Created server config for {server_id} with tools: {tool_names}")
    
    def _get_llm_provider(self, provider_name: str, server_id: str) -> BaseLLMProvider:
        """Get or create LLM provider instance."""
        cache_key = f"{server_id}:{provider_name}"
        
        if cache_key not in self.llm_providers:
            self.llm_providers[cache_key] = LLMProviderFactory.create_provider(provider_name)
        
        return self.llm_providers[cache_key]
    
    async def _send_response(self, message: discord.Message, content: str):
        """Send response as a reply, splitting if necessary."""
        # Check if content is empty or None
        if not content or not content.strip():
            logger.warning("Attempted to send empty response, sending default message instead")
            content = "I apologize, but I couldn't generate a proper response. Please try again."
        
        max_length = self.config_manager.get('bot.max_message_length', 2000)
        
        if len(content) <= max_length:
            await message.reply(content, mention_author=False)
        else:
            # Split into chunks
            chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
            # Reply to first chunk, send rest normally
            await message.reply(chunks[0], mention_author=False)
            for chunk in chunks[1:]:
                await message.channel.send(chunk)
    
    def _log_usage(self, server_id: str, user_id: str, config: Dict, response):
        """Log usage statistics to database."""
        import sqlite3
        
        cost = self._get_llm_provider(
            config.get('llm_provider'),
            server_id
        ).estimate_cost(response.usage, config.get('llm_model'))
        
        with sqlite3.connect(self.config_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usage_stats 
                (server_id, user_id, provider, model, tokens_used, cost_usd)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                server_id,
                user_id,
                config.get('llm_provider'),
                config.get('llm_model'),
                response.usage.get('total_tokens', 0),
                cost
            ))
            conn.commit()
    
    def _log_tool_call(self, server_id: str, user_id: str, tool_name: str, 
                       parameters: str, result: str, success: bool, error_message: Optional[str] = None):
        """Log tool call to database."""
        import sqlite3
        
        with sqlite3.connect(self.config_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tool_calls 
                (server_id, user_id, tool_name, parameters, result, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                server_id,
                user_id,
                tool_name,
                parameters,
                result,
                1 if success else 0,
                error_message
            ))
            conn.commit()
    
    async def _start_dashboard(self):
        """Start the web dashboard."""
        try:
            from dashboard.app import create_app
            
            app = create_app(self.config_manager, self)
            host = self.config_manager.get('dashboard.host', '127.0.0.1')
            port = self.config_manager.get('dashboard.port', 5000)
            
            logger.info(f"Starting dashboard at http://{host}:{port}")
            
            # Run Flask in a separate thread
            import threading
            def run_dashboard():
                app.run(host=host, port=port, debug=False, use_reloader=False)
            
            thread = threading.Thread(target=run_dashboard, daemon=True)
            thread.start()
        
        except ImportError:
            logger.warning("Dashboard dependencies not available")
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
    
    async def start(self):
        """Start the bot."""
        token = os.getenv('DISCORD_TOKEN')
        
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment variables")
        
        try:
            await self.bot.start(token)
        except KeyboardInterrupt:
            await self.bot.close()
