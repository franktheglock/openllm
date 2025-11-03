"""
Plugin loader and manager.
"""
import os
import json
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

from src.tools.base import BaseTool
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PluginManifest:
    """Represents a plugin manifest."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize manifest from dictionary."""
        self.name = data.get('name')
        self.version = data.get('version')
        self.author = data.get('author')
        self.description = data.get('description')
        self.permissions = data.get('permissions', [])
        self.tools = data.get('tools', [])
        self.entry_point = data.get('entry_point', 'plugin.py')
    
    def validate(self) -> bool:
        """Validate manifest has required fields."""
        required = ['name', 'version', 'author', 'description']
        return all(hasattr(self, field) and getattr(self, field) for field in required)


class PluginManager:
    """Manages loading and execution of plugins."""
    
    def __init__(self, plugins_dir: str = "plugins", config_manager=None):
        """
        Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugins
            config_manager: Configuration manager instance
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.config_manager = config_manager
        
        # Loaded plugins
        self.plugins: Dict[str, Any] = {}
        self.tools: Dict[str, BaseTool] = {}
        
        logger.info(f"Plugin manager initialized (dir: {self.plugins_dir})")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory.
        
        Returns:
            List of plugin names
        """
        plugins = []
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                manifest_file = item / 'manifest.json'
                if manifest_file.exists():
                    plugins.append(item.name)
        
        return plugins
    
    def load_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """
        Load plugin manifest.
        
        Args:
            plugin_name: Name of the plugin
        
        Returns:
            PluginManifest or None if not found/invalid
        """
        manifest_path = self.plugins_dir / plugin_name / 'manifest.json'
        
        if not manifest_path.exists():
            logger.error(f"Manifest not found for plugin: {plugin_name}")
            return None
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manifest = PluginManifest(data)
            
            if not manifest.validate():
                logger.error(f"Invalid manifest for plugin: {plugin_name}")
                return None
            
            return manifest
        
        except Exception as e:
            logger.error(f"Error loading manifest for {plugin_name}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
        
        Returns:
            True if loaded successfully
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin already loaded: {plugin_name}")
            return True
        
        # Load manifest
        manifest = self.load_manifest(plugin_name)
        if not manifest:
            return False
        
        # Check permissions
        if not self._check_permissions(manifest.permissions):
            logger.error(f"Plugin {plugin_name} requires unauthorized permissions")
            return False
        
        # Load plugin module
        try:
            plugin_path = self.plugins_dir / plugin_name
            entry_point = plugin_path / manifest.entry_point
            
            if not entry_point.exists():
                logger.error(f"Entry point not found: {entry_point}")
                return False
            
            # Add plugin directory to path
            sys.path.insert(0, str(plugin_path))
            
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}",
                entry_point
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Remove from path
            sys.path.pop(0)
            
            # Get plugin instance
            if hasattr(module, 'Plugin'):
                plugin_instance = module.Plugin()
                self.plugins[plugin_name] = {
                    'manifest': manifest,
                    'module': module,
                    'instance': plugin_instance
                }
                
                # Register tools
                if hasattr(plugin_instance, 'get_tools'):
                    tools = plugin_instance.get_tools()
                    for tool in tools:
                        tool_name = tool.get_definition().name
                        self.tools[tool_name] = tool
                        logger.info(f"Registered tool from plugin: {tool_name}")
                
                logger.info(f"Loaded plugin: {plugin_name} v{manifest.version}")
                return True
            else:
                logger.error(f"Plugin {plugin_name} has no Plugin class")
                return False
        
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}", exc_info=True)
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
        
        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self.plugins:
            return False
        
        # Remove tools
        plugin_data = self.plugins[plugin_name]
        instance = plugin_data.get('instance')
        
        if instance and hasattr(instance, 'get_tools'):
            tools = instance.get_tools()
            for tool in tools:
                tool_name = tool.get_definition().name
                if tool_name in self.tools:
                    del self.tools[tool_name]
        
        # Call cleanup if available
        if instance and hasattr(instance, 'cleanup'):
            try:
                instance.cleanup()
            except Exception as e:
                logger.error(f"Error during plugin cleanup: {e}")
        
        # Remove plugin
        del self.plugins[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")
        return True
    
    def load_all_plugins(self):
        """Load all discovered plugins."""
        plugins = self.discover_plugins()
        
        for plugin_name in plugins:
            # Check if enabled in database
            if self.config_manager:
                with sqlite3.connect(self.config_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT enabled FROM plugins WHERE name = ?",
                        (plugin_name,)
                    )
                    result = cursor.fetchone()
                    
                    if result and not result[0]:
                        logger.info(f"Skipping disabled plugin: {plugin_name}")
                        continue
            
            self.load_plugin(plugin_name)
    
    def _check_permissions(self, permissions: List[str]) -> bool:
        """
        Check if permissions are allowed.
        
        Args:
            permissions: List of requested permissions
        
        Returns:
            True if all permissions are allowed
        """
        if not self.config_manager:
            return True
        
        allowed = self.config_manager.get('plugins.allowed_permissions', [])
        
        for perm in permissions:
            if perm not in allowed:
                return False
        
        return True
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a loaded plugin.
        
        Args:
            plugin_name: Name of the plugin
        
        Returns:
            Plugin info dictionary or None
        """
        if plugin_name not in self.plugins:
            return None
        
        plugin_data = self.plugins[plugin_name]
        manifest = plugin_data['manifest']
        
        return {
            'name': manifest.name,
            'version': manifest.version,
            'author': manifest.author,
            'description': manifest.description,
            'permissions': manifest.permissions,
            'tools': [t.name for t in manifest.tools]
        }
