"""
Flask web dashboard for bot configuration and monitoring.
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from src.config.manager import ConfigManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app(config_manager: Optional[ConfigManager] = None, bot = None):
    """
    Create and configure the Flask app.
    
    Args:
        config_manager: Configuration manager instance
        bot: Discord bot instance
    
    Returns:
        Flask app
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    CORS(app)
    
    # Store references
    app.config_manager = config_manager or ConfigManager()
    app.bot = bot
    
    @app.route('/')
    def index():
        """Dashboard home page."""
        return render_template('index.html')
    
    @app.route('/marketplace')
    def marketplace():
        """Plugin marketplace page."""
        return render_template('marketplace.html')
    
    @app.route('/api/status')
    def api_status():
        """Get bot status."""
        status = {
            'online': app.bot is not None and app.bot.bot.is_ready() if app.bot else False,
            'servers': len(app.bot.bot.guilds) if app.bot and app.bot.bot.is_ready() else 0,
            'uptime': 'N/A'  # TODO: Track uptime
        }
        return jsonify(status)
    
    @app.route('/api/config')
    def api_config():
        """Get current configuration."""
        return jsonify(app.config_manager.config)
    
    @app.route('/api/config', methods=['POST'])
    def api_update_config():
        """Update configuration."""
        try:
            data = request.json
            
            # Update configuration
            for key, value in data.items():
                app.config_manager.set(key, value)
            
            # Reload bot configuration if bot is running
            if app.bot:
                app.bot._load_tools()
            
            return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/servers')
    def api_servers():
        """Get list of connected servers."""
        if not app.bot or not app.bot.bot.is_ready():
            return jsonify([])
        
        servers = []
        for guild in app.bot.bot.guilds:
            server_config = app.config_manager.get_server_config(str(guild.id))
            servers.append({
                'id': str(guild.id),
                'name': guild.name,
                'member_count': guild.member_count,
                'llm_provider': server_config.get('llm_provider'),
                'llm_model': server_config.get('llm_model')
            })
        
        return jsonify(servers)
    
    @app.route('/api/servers/<server_id>/config', methods=['GET', 'POST'])
    def api_server_config(server_id):
        """Get or update server-specific configuration."""
        if request.method == 'GET':
            config = app.config_manager.get_server_config(server_id)
            return jsonify(config)
        else:
            config = request.json
            app.config_manager.set_server_config(server_id, config)
            # If the bot is running, ask it to refresh in-memory structures for this server
            try:
                if app.bot and hasattr(app.bot, 'refresh_server_config'):
                    app.bot.refresh_server_config(server_id)
            except Exception as e:
                logger.error(f"Error refreshing bot server config for {server_id}: {e}")
            return jsonify({'success': True})
    
    @app.route('/api/usage/stats')
    def api_usage_stats():
        """Get usage statistics."""
        days = request.args.get('days', 7, type=int)
        
        with sqlite3.connect(app.config_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Total usage
            cursor.execute("""
                SELECT 
                    COUNT(*) as requests,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_usd) as total_cost
                FROM usage_stats
                WHERE timestamp > datetime('now', '-' || ? || ' days')
            """, (days,))
            
            row = cursor.fetchone()
            total_stats = {
                'requests': row[0] or 0,
                'tokens': row[1] or 0,
                'cost': row[2] or 0.0
            }
            
            # Per-provider stats
            cursor.execute("""
                SELECT 
                    provider,
                    COUNT(*) as requests,
                    SUM(tokens_used) as tokens,
                    SUM(cost_usd) as cost
                FROM usage_stats
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                GROUP BY provider
            """, (days,))
            
            provider_stats = []
            for row in cursor.fetchall():
                provider_stats.append({
                    'provider': row[0],
                    'requests': row[1],
                    'tokens': row[2],
                    'cost': row[3]
                })
            
            # Daily breakdown
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as requests,
                    SUM(tokens_used) as tokens,
                    SUM(cost_usd) as cost
                FROM usage_stats
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (days,))
            
            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    'date': row[0],
                    'requests': row[1],
                    'tokens': row[2],
                    'cost': row[3]
                })
        
        return jsonify({
            'total': total_stats,
            'by_provider': provider_stats,
            'daily': daily_stats
        })
    
    @app.route('/api/tools')
    def api_tools():
        """Get available tools."""
        if not app.bot:
            return jsonify([])
        
        tools = []
        for name, tool in app.bot.tools.items():
            definition = tool.get_definition()
            tools.append({
                'name': definition.name,
                'description': definition.description,
                'enabled': True
            })
        
        return jsonify(tools)
    
    @app.route('/api/plugins')
    def api_plugins():
        """Get installed plugins (from filesystem and database)."""
        import json
        from pathlib import Path
        
        plugins_dir = Path('plugins')
        plugins = []
        
        # Get database plugin states
        db_plugins = {}
        try:
            with sqlite3.connect(app.config_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, version, enabled FROM plugins")
                for row in cursor.fetchall():
                    db_plugins[row[0]] = {
                        'version': row[1],
                        'enabled': bool(row[2])
                    }
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            pass
        
        # Scan filesystem for actual plugins
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                
                manifest_path = plugin_dir / 'manifest.json'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            plugin_name = manifest.get('name', plugin_dir.name)
                            
                            # Get state from database if available
                            db_info = db_plugins.get(plugin_name, {})
                            
                            plugins.append({
                                'name': plugin_name,
                                'version': db_info.get('version', manifest.get('version', '1.0.0')),
                                'enabled': db_info.get('enabled', manifest.get('builtin', False))
                            })
                    except Exception as e:
                        print(f"Error loading plugin manifest {plugin_dir.name}: {e}")
        
        return jsonify(plugins)
    
    @app.route('/api/providers')
    def api_providers():
        """Get available LLM providers and models."""
        from src.llm.factory import LLMProviderFactory
        import asyncio
        import os
        
        providers = []
        provider_info = {
            'gemini': {
                'name': 'Google Gemini',
                'description': 'Fast, affordable, and powerful',
                'recommended': True,
                'env_var': 'GEMINI_API_KEY'
            },
            'openai': {
                'name': 'OpenAI',
                'description': 'GPT-4 and GPT-3.5 models',
                'recommended': False,
                'env_var': 'OPENAI_API_KEY'
            },
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Claude 3 family',
                'recommended': False,
                'env_var': 'ANTHROPIC_API_KEY'
            },
            'ollama': {
                'name': 'Ollama',
                'description': 'Local models (free)',
                'recommended': False,
                'env_var': None  # No API key needed
            },
            'openrouter': {
                'name': 'OpenRouter',
                'description': 'Access to multiple providers',
                'recommended': False,
                'env_var': 'OPENROUTER_API_KEY'
            },
            'lmstudio': {
                'name': 'LM Studio',
                'description': 'Local LM Studio server',
                'recommended': False,
                'env_var': None  # No API key needed
            },
            'custom': {
                'name': 'Custom Endpoint',
                'description': 'OpenAI-compatible API endpoint',
                'recommended': False,
                'env_var': 'CUSTOM_API_KEY'
            }
        }
        
        for provider_name in LLMProviderFactory.get_available_providers():
            info = provider_info.get(provider_name, {})
            env_var = info.get('env_var')
            
            # Check if provider is configured (has API key or doesn't need one)
            is_configured = False
            endpoint = None
            
            if env_var is None:  # Ollama, LM Studio, etc.
                # Check if endpoint is configured
                if provider_name == 'lmstudio':
                    endpoint = os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')
                    is_configured = True
                elif provider_name == 'ollama':
                    endpoint = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                    is_configured = True
                elif provider_name == 'custom':
                    endpoint = os.getenv('CUSTOM_OPENAI_BASE_URL')
                    api_key = os.getenv('CUSTOM_OPENAI_API_KEY')
                    is_configured = bool(endpoint and endpoint.strip())
            elif env_var:
                api_key = os.getenv(env_var)
                is_configured = bool(api_key and api_key.strip() and api_key != f'your_{env_var.lower()}')
            
            try:
                if is_configured:
                    # Try to create provider to get available models
                    provider = LLMProviderFactory.create_provider(provider_name)
                    
                    # For OpenRouter, try to fetch models from API
                    if provider_name == 'openrouter' and hasattr(provider, 'fetch_models_from_api'):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            models = loop.run_until_complete(provider.fetch_models_from_api())
                            loop.close()
                        except:
                            models = provider.get_available_models()
                    else:
                        models = provider.get_available_models()
                    
                    providers.append({
                        'name': provider_name,
                        'display_name': info.get('name', provider_name.title()),
                        'description': info.get('description', ''),
                        'recommended': info.get('recommended', False),
                        'models': models,
                        'available': True,
                        'configured': True,
                        'env_var': env_var,
                        'endpoint': endpoint
                    })
                else:
                    providers.append({
                        'name': provider_name,
                        'display_name': info.get('name', provider_name.title()),
                        'description': info.get('description', ''),
                        'recommended': info.get('recommended', False),
                        'models': [],
                        'available': False,
                        'configured': False,
                        'env_var': env_var,
                        'endpoint': endpoint
                    })
            except Exception as e:
                logger.error(f"Error loading provider {provider_name}: {e}")
                providers.append({
                    'name': provider_name,
                    'display_name': info.get('name', provider_name.title()),
                    'description': info.get('description', ''),
                    'recommended': info.get('recommended', False),
                    'models': [],
                    'available': False,
                    'configured': is_configured,
                    'env_var': env_var,
                    'endpoint': endpoint
                })
        
        return jsonify(providers)
    
    @app.route('/api/providers/config', methods=['POST'])
    def api_save_provider_config():
        """Save provider configuration (API keys, endpoints)."""
        try:
            data = request.json
            provider = data.get('provider')
            api_key = data.get('api_key')
            endpoint = data.get('endpoint')
            env_var = data.get('env_var')
            
            if not provider:
                return jsonify({'success': False, 'error': 'Provider name required'}), 400
            
            # Load or create .env file
            env_path = Path(__file__).parent.parent / '.env'
            env_vars = {}
            
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            # Update configuration based on provider type
            if provider in ['lmstudio', 'ollama']:
                # Save endpoint for local providers
                if endpoint:
                    env_key = f'{provider.upper()}_BASE_URL'
                    env_vars[env_key] = endpoint
            elif provider == 'custom':
                # Save both endpoint and API key for custom provider
                if endpoint:
                    env_vars['CUSTOM_OPENAI_BASE_URL'] = endpoint
                if api_key:
                    env_vars['CUSTOM_OPENAI_API_KEY'] = api_key
            else:
                # Save API key for standard providers
                if env_var and api_key is not None:
                    if api_key:
                        env_vars[env_var] = api_key
                    else:
                        # Remove the key if empty string is provided
                        env_vars.pop(env_var, None)
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f'{key}={value}\n')
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Failed to save provider config: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/config/llm', methods=['POST'])
    def api_update_llm_config():
        """Update LLM configuration."""
        try:
            data = request.json
            
            if 'provider' in data:
                app.config_manager.set('llm.default_provider', data['provider'])
            
            if 'model' in data:
                app.config_manager.set('llm.default_model', data['model'])
            
            if 'temperature' in data:
                app.config_manager.set('llm.temperature', float(data['temperature']))
            
            if 'max_tokens' in data:
                app.config_manager.set('llm.max_tokens', int(data['max_tokens']))
            
            if 'system_prompt' in data:
                app.config_manager.set('llm.system_prompt', data['system_prompt'])
            
            return jsonify({'success': True, 'message': 'LLM configuration updated'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/config/llm/generate-prompt', methods=['POST'])
    def api_generate_prompt():
        """Use AI to generate/enhance a system prompt."""
        try:
            import asyncio
            from src.llm.factory import LLMProviderFactory
            from src.llm.base import Message
            
            data = request.json
            prompt = data.get('prompt', '')
            server_id = data.get('server_id')
            
            if not prompt:
                return jsonify({'success': False, 'error': 'No prompt provided'}), 400
            
            # Get server config or use defaults
            if server_id:
                config = app.config_manager.get_server_config(server_id)
            else:
                config = {
                    'llm_provider': app.config_manager.get('llm.default_provider'),
                    'llm_model': app.config_manager.get('llm.default_model'),
                    'temperature': 0.7,
                    'max_tokens': 500
                }
            
            # Create LLM provider
            provider = LLMProviderFactory.create_provider(config['llm_provider'])
            
            # Generate the enhanced prompt
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Optionally include web-search tool(s) if requested
                include_search = bool(data.get('include_search', True))
                tool_defs = None
                if include_search and app.bot:
                    tool_defs = []
                    for _, tool in app.bot.tools.items():
                        try:
                            # Use tool definition name heuristics to find search tools
                            tdef = tool.get_definition()
                            tname = (tdef.name or '').lower()
                            if 'search' in tname or 'web' in tname:
                                # Convert to OpenAI-compatible tool descriptor
                                if hasattr(tool, 'to_openai_tool'):
                                    tool_defs.append(tool.to_openai_tool())
                        except Exception:
                            continue

                # Prepare initial messages
                messages_for_model = [Message(role='user', content=prompt)]

                # If include_search requested and bot is available, build tool definitions
                include_search = bool(data.get('include_search', True))
                tool_definitions = None
                if include_search and app.bot:
                    tool_definitions = []
                    for _, tool in app.bot.tools.items():
                        try:
                            if hasattr(tool, 'to_openai_tool'):
                                tdef = tool.get_definition()
                                tname = (tdef.name or '').lower()
                                # Only expose search-like tools for prompt generation
                                if 'search' in tname or 'web' in tname:
                                    tool_definitions.append(tool.to_openai_tool())
                        except Exception:
                            continue

                # Determine whether multi-step tool calling is allowed (UI toggle)
                allow_multistep = bool(data.get('allow_multistep', False))

                response = None
                if allow_multistep:
                    # Multi-step loop: let the model call tools, execute them, append results,
                    # and re-call the model until no tool_calls or max depth reached.
                    max_depth = 5
                    final_response = None
                    for depth in range(max_depth):
                        response = loop.run_until_complete(provider.complete(
                            messages=messages_for_model,
                            model=config['llm_model'],
                            temperature=config['temperature'],
                            max_tokens=config.get('max_tokens', 500),
                            tools=tool_definitions
                        ))

                        # If provider returned tool calls, execute them via app.bot.tools
                        if response and getattr(response, 'tool_calls', None):
                            for tool_call in response.tool_calls:
                                try:
                                    tool_name = tool_call['function']['name']
                                    tool_args_str = tool_call['function'].get('arguments')
                                    # Robust argument parsing: accept dict, bytes, or JSON/text
                                    import json as _json
                                    tool_args = {}
                                    try:
                                        if isinstance(tool_args_str, dict):
                                            tool_args = tool_args_str
                                        elif isinstance(tool_args_str, (bytes, bytearray)):
                                            try:
                                                tool_args = _json.loads(tool_args_str.decode('utf-8'))
                                            except Exception:
                                                tool_args = {}
                                        elif isinstance(tool_args_str, str):
                                            try:
                                                tool_args = _json.loads(tool_args_str)
                                            except Exception:
                                                try:
                                                    from ast import literal_eval as _literal_eval
                                                    tool_args = _literal_eval(tool_args_str)
                                                except Exception:
                                                    tool_args = {}
                                        else:
                                            tool_args = {}
                                    except Exception:
                                        tool_args = {}

                                    result = None
                                    if app.bot and tool_name in app.bot.tools:
                                        tool = app.bot.tools[tool_name]
                                        fn = getattr(tool, 'execute', None)
                                        if fn:
                                            try:
                                                res = fn(**(tool_args or {}))
                                                if asyncio.iscoroutine(res):
                                                    result = loop.run_until_complete(res)
                                                else:
                                                    result = res
                                            except TypeError:
                                                # Try passing as single argument
                                                try:
                                                    res = fn(tool_args)
                                                    if asyncio.iscoroutine(res):
                                                        result = loop.run_until_complete(res)
                                                    else:
                                                        result = res
                                                except Exception as e:
                                                    result = f"Tool execution failed: {e}"
                                            except Exception as e:
                                                result = f"Tool execution failed: {e}"
                                    else:
                                        result = f"Tool {tool_name} not found"

                                    # Append tool result as a tool-role message for the model
                                    # Prefix with tool name so providers pick up the source
                                    messages_for_model.append(Message(role='tool', content=f"[{tool_name}] {result}"))
                                except Exception as e:
                                    # Continue to next tool call on error
                                    logger.error(f"Error executing tool call in generate-prompt: {e}")
                                    messages_for_model.append(Message(role='tool', content=f"Error executing tool: {e}"))

                            # Continue loop to let model process tool outputs
                            continue

                        # No tool calls - use this response
                        final_response = response
                        break

                    response = final_response
                else:
                    # Single-step flow: call provider once with tools; if it returns tool_calls,
                    # execute them one time and then call the provider once more without tools
                    try:
                        initial = loop.run_until_complete(provider.complete(
                            messages=messages_for_model,
                            model=config['llm_model'],
                            temperature=config['temperature'],
                            max_tokens=config.get('max_tokens', 500),
                            tools=tool_definitions
                        ))
                        # If model asked for tool calls, execute each once and append results
                        if initial and getattr(initial, 'tool_calls', None):
                            for tool_call in initial.tool_calls:
                                try:
                                    tool_name = tool_call['function']['name']
                                    tool_args_str = tool_call['function'].get('arguments')
                                    import json as _json
                                    tool_args = {}
                                    try:
                                        if isinstance(tool_args_str, dict):
                                            tool_args = tool_args_str
                                        elif isinstance(tool_args_str, (bytes, bytearray)):
                                            try:
                                                tool_args = _json.loads(tool_args_str.decode('utf-8'))
                                            except Exception:
                                                tool_args = {}
                                        elif isinstance(tool_args_str, str):
                                            try:
                                                tool_args = _json.loads(tool_args_str)
                                            except Exception:
                                                try:
                                                    from ast import literal_eval as _literal_eval
                                                    tool_args = _literal_eval(tool_args_str)
                                                except Exception:
                                                    tool_args = {}
                                        else:
                                            tool_args = {}
                                    except Exception:
                                        tool_args = {}

                                    result = None
                                    if app.bot and tool_name in app.bot.tools:
                                        tool = app.bot.tools[tool_name]
                                        fn = getattr(tool, 'execute', None)
                                        if fn:
                                            try:
                                                res = fn(**(tool_args or {}))
                                                if asyncio.iscoroutine(res):
                                                    result = loop.run_until_complete(res)
                                                else:
                                                    result = res
                                            except Exception as e:
                                                result = f"Tool execution failed: {e}"
                                    else:
                                        result = f"Tool {tool_name} not found"

                                    messages_for_model.append(Message(role='tool', content=str(result)))
                                except Exception as e:
                                    logger.error(f"Error executing single-step tool call: {e}")
                                    messages_for_model.append(Message(role='tool', content=f"Error executing tool: {e}"))

                        # After executing tool calls once, request final synthesis without tools
                        response = loop.run_until_complete(provider.complete(
                            messages=messages_for_model,
                            model=config['llm_model'],
                            temperature=config['temperature'],
                            max_tokens=config.get('max_tokens', 500),
                            tools=None
                        ))
                    except Exception as e:
                        logger.error(f"Error in single-step prompt generation: {e}")
                        response = None

                # If we didn't get a usable response, try one final attempt without tools
                if not response or not getattr(response, 'content', None) or not str(response.content).strip():
                    try:
                        fallback = loop.run_until_complete(provider.complete(
                            messages=messages_for_model,
                            model=config['llm_model'],
                            temperature=config['temperature'],
                            max_tokens=config.get('max_tokens', 500),
                            tools=None
                        ))
                        response = fallback
                    except Exception as e:
                        logger.error(f"Fallback generate-prompt call failed: {e}")

                if not response or not getattr(response, 'content', None) or not str(response.content).strip():
                    logger.error(f"Generate-prompt: no content returned. final_response={final_response}")
                    return jsonify({'success': False, 'error': 'No prompt returned'})

                enhanced_prompt = str(response.content).strip()
                return jsonify({'success': True, 'prompt': enhanced_prompt})
            finally:
                loop.close()
                
        except Exception as e:
            import traceback
            print(f"Error generating prompt: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/logs')
    def api_logs():
        """Get recent bot logs."""
        import os
        from pathlib import Path
        
        log_file = Path('logs/bot.log')
        if not log_file.exists():
            return jsonify({'logs': []})
        
        # Read last 500 lines
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-500:] if len(lines) > 500 else lines
                return jsonify({'logs': [line.strip() for line in recent_lines]})
        except Exception as e:
            return jsonify({'logs': [], 'error': str(e)})
    
    @app.route('/api/tool_calls')
    def api_tool_calls():
        """Get recent tool calls with parameters."""
        limit = request.args.get('limit', 100, type=int)
        
        with sqlite3.connect(app.config_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, server_id, user_id, tool_name, parameters, result, 
                       success, error_message, timestamp
                FROM tool_calls
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            tool_calls = []
            for row in cursor.fetchall():
                import json
                tool_calls.append({
                    'id': row[0],
                    'server_id': row[1],
                    'user_id': row[2],
                    'tool_name': row[3],
                    'parameters': json.loads(row[4]) if row[4] else {},
                    'result': row[5],
                    'success': bool(row[6]),
                    'error_message': row[7],
                    'timestamp': row[8]
                })
        
        return jsonify(tool_calls)
    
    @app.route('/api/marketplace/plugins')
    def api_marketplace_plugins():
        """Get available plugins from marketplace."""
        import os
        import json
        from pathlib import Path
        
        plugins_dir = Path('plugins')
        available_plugins = []
        
        # Scan plugins directory
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    manifest_path = plugin_dir / 'manifest.json'
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if not content:
                                    print(f"Skipping plugin {plugin_dir.name}: Empty manifest.json")
                                    continue
                                manifest = json.loads(content)
                                
                                # Check if plugin is installed
                                installed = False
                                with sqlite3.connect(app.config_manager.db_path) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("SELECT 1 FROM plugins WHERE name = ?", (manifest['name'],))
                                    installed = cursor.fetchone() is not None
                                
                                available_plugins.append({
                                    'id': plugin_dir.name,
                                    'name': manifest.get('name', plugin_dir.name),
                                    'version': manifest.get('version', '1.0.0'),
                                    'author': manifest.get('author', 'Unknown'),
                                    'description': manifest.get('description', ''),
                                    'icon': manifest.get('icon', '🔌'),
                                    'category': manifest.get('category', 'utility'),
                                    'tags': manifest.get('tags', []),
                                    'installed': installed,
                                    'builtin': manifest.get('builtin', False),
                                    'tools': manifest.get('tools', [])
                                })
                        except Exception as e:
                            print(f"Error loading plugin {plugin_dir.name}: {e}")
        
        return jsonify(available_plugins)
    
    @app.route('/api/marketplace/install/<plugin_id>', methods=['POST'])
    def api_install_plugin(plugin_id):
        """Install a plugin."""
        import json
        from pathlib import Path
        import importlib.util
        
        try:
            plugins_dir = Path('plugins')
            plugin_dir = plugins_dir / plugin_id
            
            if not plugin_dir.exists():
                return jsonify({'success': False, 'error': 'Plugin not found'}), 404
            
            manifest_path = plugin_dir / 'manifest.json'
            if not manifest_path.exists():
                return jsonify({'success': False, 'error': 'Plugin manifest not found'}), 404
            
            # Load manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check if already installed
            with sqlite3.connect(app.config_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM plugins WHERE name = ?", (manifest['name'],))
                if cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Plugin already installed'}), 400
                
                # Install plugin in database
                cursor.execute("""
                    INSERT INTO plugins (name, version, enabled, config_json)
                    VALUES (?, ?, 1, '{}')
                """, (manifest['name'], manifest['version']))
                conn.commit()
            
            # Reload bot tools if bot is running
            if app.bot:
                app.bot._load_tools()
                
                # Update all server configs to include the new tools
                # Get all tool names
                tool_names = list(app.bot.tools.keys())
                
                # Update each server's enabled_tools
                with sqlite3.connect(app.config_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT server_id, enabled_tools FROM server_config")
                    servers = cursor.fetchall()
                    
                    for server_id, enabled_tools in servers:
                        # Update to include all tools
                        cursor.execute("""
                            UPDATE server_config 
                            SET enabled_tools = ? 
                            WHERE server_id = ?
                        """, (','.join(tool_names), server_id))
                    
                    conn.commit()
                
                print(f"Updated server configs with tools: {tool_names}")
            
            return jsonify({
                'success': True,
                'message': f"Plugin '{manifest['name']}' installed successfully",
                'plugin': {
                    'name': manifest['name'],
                    'version': manifest['version']
                }
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error installing plugin: {error_details}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/marketplace/uninstall/<plugin_id>', methods=['POST'])
    def api_uninstall_plugin(plugin_id):
        """Uninstall a plugin."""
        import json
        from pathlib import Path
        
        try:
            plugins_dir = Path('plugins')
            plugin_dir = plugins_dir / plugin_id
            
            if not plugin_dir.exists():
                return jsonify({'success': False, 'error': 'Plugin not found'}), 404
            
            manifest_path = plugin_dir / 'manifest.json'
            if not manifest_path.exists():
                return jsonify({'success': False, 'error': 'Plugin manifest not found'}), 404
            
            # Load manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Remove from database
            with sqlite3.connect(app.config_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM plugins WHERE name = ?", (manifest['name'],))
                conn.commit()
            
            # Reload bot tools if bot is running
            if app.bot:
                app.bot._load_tools()
            
            return jsonify({
                'success': True,
                'message': f"Plugin '{manifest['name']}' uninstalled successfully"
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/sync', methods=['POST'])
    def api_sync_tools():
        """Sync all loaded tools to all server configurations."""
        try:
            import json
            
            if not app.bot:
                return jsonify({'success': False, 'error': 'Bot not running'}), 400
            
            # Get all tool names
            tool_names = list(app.bot.tools.keys())
            
            # Update each server's enabled_tools
            with sqlite3.connect(app.config_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT server_id FROM server_config")
                servers = cursor.fetchall()
                
                updated_count = 0
                for (server_id,) in servers:
                    cursor.execute("""
                        UPDATE server_config 
                        SET enabled_tools = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE server_id = ?
                    """, (','.join(tool_names), server_id))
                    updated_count += 1
                
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Synced {len(tool_names)} tools to {updated_count} server(s)',
                'tools': tool_names
            })
            
        except Exception as e:
            import traceback
            print(f"Error syncing tools: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/available')
    def api_available_tools():
        """Get all available tools with their status."""
        try:
            import json
            from pathlib import Path
            
            tools_info = []
            
            if not app.bot:
                return jsonify({'success': False, 'error': 'Bot not running'}), 400
            
            # Get all loaded tools from bot
            for tool_name, tool in app.bot.tools.items():
                tool_def = tool.get_definition()
                
                # Find plugin info if it's from a plugin
                plugin_info = None
                builtin = False
                
                plugins_dir = Path('plugins')
                if plugins_dir.exists():
                    for plugin_dir in plugins_dir.iterdir():
                        if not plugin_dir.is_dir():
                            continue
                        
                        manifest_path = plugin_dir / 'manifest.json'
                        if manifest_path.exists():
                            try:
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    if not content:
                                        continue
                                    manifest = json.loads(content)
                                    
                                    # Check if this tool belongs to this plugin
                                    tool_names_in_plugin = [t.get('name') for t in manifest.get('tools', [])]
                                    if tool_name in tool_names_in_plugin:
                                        plugin_info = {
                                            'name': manifest.get('name'),
                                            'icon': manifest.get('icon', '🔌'),
                                            'author': manifest.get('author', 'Unknown')
                                        }
                                        builtin = manifest.get('builtin', False)
                                        break
                            except (json.JSONDecodeError, KeyError) as e:
                                # Skip invalid manifests
                                continue
                
                # Check if tool is enabled (get from first server config)
                enabled = False
                with sqlite3.connect(app.config_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT enabled_tools FROM server_config LIMIT 1")
                    result = cursor.fetchone()
                    if result and result[0]:
                        enabled_tools = result[0].split(',')
                        enabled = tool_name in enabled_tools
                
                tools_info.append({
                    'name': tool_name,
                    'description': tool_def.description,
                    'enabled': enabled,
                    'builtin': builtin,
                    'plugin': plugin_info
                })
            
            return jsonify({'success': True, 'tools': tools_info})
            
        except Exception as e:
            import traceback
            print(f"Error getting available tools: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/toggle/<tool_name>', methods=['POST'])
    def api_toggle_tool(tool_name):
        """Toggle a tool on/off for all servers."""
        try:
            data = request.json or {}
            enabled = data.get('enabled', True)
            
            # Update all server configs
            with sqlite3.connect(app.config_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT server_id, enabled_tools FROM server_config")
                servers = cursor.fetchall()
                
                for server_id, enabled_tools_str in servers:
                    enabled_tools = enabled_tools_str.split(',') if enabled_tools_str else []
                    
                    if enabled:
                        # Add tool if not present
                        if tool_name not in enabled_tools:
                            enabled_tools.append(tool_name)
                    else:
                        # Remove tool if present
                        if tool_name in enabled_tools:
                            enabled_tools.remove(tool_name)
                    
                    cursor.execute("""
                        UPDATE server_config 
                        SET enabled_tools = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE server_id = ?
                    """, (','.join(enabled_tools), server_id))
                
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Tool {tool_name} {"enabled" if enabled else "disabled"}',
                'tool_name': tool_name,
                'enabled': enabled
            })
            
        except Exception as e:
            import traceback
            print(f"Error toggling tool: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app



if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
