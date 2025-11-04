"""
Configuration manager for the bot.
Handles loading, saving, and runtime updates of configuration.
"""
import os
import yaml
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfigManager:
    """Manages bot configuration from YAML, environment, and database."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.db_path = Path("data/bot.db")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize database
        self._init_database()
        
        # Load configuration
        self.reload()
    
    def _init_database(self):
        """Initialize the SQLite database for per-server configurations."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Server configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_config (
                    server_id TEXT PRIMARY KEY,
                    llm_provider TEXT,
                    llm_model TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    system_prompt TEXT,
                    enabled_tools TEXT,
                    enforce_char_limit INTEGER DEFAULT 0,
                    config_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT,
                    user_id TEXT,
                    provider TEXT,
                    model TEXT,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Plugin management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    name TEXT PRIMARY KEY,
                    version TEXT,
                    enabled INTEGER DEFAULT 1,
                    config_json TEXT,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tool calls logging
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT,
                    user_id TEXT,
                    tool_name TEXT,
                    parameters TEXT,
                    result TEXT,
                    success INTEGER,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Migrate existing databases to add enforce_char_limit column if it doesn't exist
            cursor.execute("PRAGMA table_info(server_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'enforce_char_limit' not in columns:
                cursor.execute("""
                    ALTER TABLE server_config 
                    ADD COLUMN enforce_char_limit INTEGER DEFAULT 0
                """)
                conn.commit()
                logger.info("Added enforce_char_limit column to server_config table")
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def reload(self):
        """Reload configuration from file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self.config = self._default_config()
            self.save()
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info("Configuration loaded")
    
    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        logger.info("Configuration saved")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'llm.default_provider')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'llm.default_provider')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def get_server_config(self, server_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific server.
        
        Args:
            server_id: Discord server ID
        
        Returns:
            Server-specific configuration
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT llm_provider, llm_model, temperature, max_tokens, system_prompt, enabled_tools, config_json FROM server_config WHERE server_id = ?",
                (server_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Build config from columns
                config = {
                    'llm_provider': result[0] or self.get('llm.default_provider'),
                    'llm_model': result[1] or self.get('llm.default_model'),
                    'temperature': result[2] if result[2] is not None else self.get('llm.temperature'),
                    'max_tokens': result[3] or self.get('llm.max_tokens'),
                    'system_prompt': result[4],
                    'enabled_tools': result[5].split(',') if result[5] else None
                }
                
                # Merge with config_json if present
                if result[6]:
                    json_config = json.loads(result[6])
                    config.update(json_config)
                
                # If enabled_tools is still None, use empty list (will be set by bot on first run)
                if config['enabled_tools'] is None:
                    config['enabled_tools'] = json_config.get('enabled_tools', []) if result[6] else []
                
                return config
            else:
                # Return default configuration - empty enabled_tools means bot will set it
                return {
                    'llm_provider': self.get('llm.default_provider'),
                    'llm_model': self.get('llm.default_model'),
                    'temperature': self.get('llm.temperature'),
                    'max_tokens': self.get('llm.max_tokens'),
                    'enabled_tools': []  # Empty list - bot will populate on startup
                }
    
    def set_server_config(self, server_id: str, config: Dict[str, Any]):
        """
        Set configuration for a specific server.
        
        Args:
            server_id: Discord server ID
            config: Configuration dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO server_config 
                (server_id, config_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (server_id, json.dumps(config)))
            conn.commit()
        
        logger.info(f"Updated config for server {server_id}")
    
    def is_configured(self) -> bool:
        """Check if the bot has been configured."""
        # Check if essential values are set
        discord_token = os.getenv('DISCORD_TOKEN')
        
        if not discord_token or discord_token == 'your_discord_bot_token_here':
            return False
        
        # Check if at least one LLM provider is configured
        providers = ['GEMINI_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY']
        has_llm = any(
            os.getenv(p) and os.getenv(p) != f'your_{p.lower()}'
            for p in providers
        )
        
        return has_llm
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'bot': {
                'prefix': '!',
                'status': 'online',
                'activity': 'Chatting with AI'
            },
            'llm': {
                'default_provider': 'openai',
                'default_model': 'gpt-4-turbo-preview',
                'temperature': 0.7,
                'max_tokens': 2048
            },
            'tools': {
                'web_search': {
                    'enabled': True,
                    'default_provider': 'duckduckgo'
                }
            },
            'logging': {
                'level': 'INFO',
                'file': './logs/bot.log'
            }
        }
