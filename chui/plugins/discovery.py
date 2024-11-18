# chui/plugins/discovery.py

import importlib
import pkgutil
import os
from pathlib import Path
from typing import Dict, Type, Iterator, Optional
from ..core.errors import PluginError, ErrorCategory
from .base import Plugin
from ..ui import UI
from ..config import Config


class PluginDiscovery:
    """Dynamic plugin discovery and loading system"""

    def __init__(self, ui: UI, config: Config):
        self.ui = ui
        self.config = config
        self.debug = self.config.get('system.debug', False)

        # Get project root (where main app.py is located)
        self.project_root = Path(os.getcwd())
        if self.debug:
            self.ui.debug(f"Project root: {self.project_root}")

        # User plugins directory
        self.plugins_dir = self.project_root / 'plugins'
        if self.debug:
            self.ui.debug(f"Plugins directory: {self.plugins_dir}")

        # Create plugins directory if it doesn't exist
        if not self.plugins_dir.exists():
            if self.debug:
                self.ui.debug("Creating plugins directory...")
            self.plugins_dir.mkdir(parents=True)
            # Create __init__.py to make it a package
            (self.plugins_dir / '__init__.py').touch()
            if self.debug:
                self.ui.debug("Created plugins directory and __init__.py")

        # Add plugins directory to Python path if not already there
        plugins_path = str(self.plugins_dir.parent)
        if plugins_path not in os.sys.path:
            if self.debug:
                self.ui.debug(f"Adding {plugins_path} to Python path")
            os.sys.path.insert(0, plugins_path)

    def discover_plugins(self) -> Dict[str, Type[Plugin]]:
        """Discover all available plugins in the plugins directory"""
        if self.debug:
            self.ui.debug("Starting plugin discovery...")
        plugins = {}

        try:
            if not self.plugins_dir.exists():
                self.ui.warning(f"Plugins directory not found: {self.plugins_dir}")
                return plugins

            if self.debug:
                self.ui.debug(f"Scanning plugins directory: {self.plugins_dir}")

            # Look for plugin directories
            for plugin_dir in self.plugins_dir.iterdir():
                if self.debug:
                    self.ui.debug(f"Checking directory: {plugin_dir}")

                if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
                    continue

                try:
                    # Import the plugin module
                    module_name = f"plugins.{plugin_dir.name}.plugin"
                    if self.debug:
                        self.ui.debug(f"Attempting to import module: {module_name}")

                    module = importlib.import_module(module_name)
                    if self.debug:
                        self.ui.debug(f"Successfully imported module: {module_name}")

                    # Look for Plugin class in module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                                issubclass(attr, Plugin) and
                                attr != Plugin):
                            # Found a plugin class
                            plugin_class = attr
                            plugin_name = getattr(plugin_class, 'name', plugin_dir.name)
                            plugins[plugin_name] = plugin_class
                            if self.debug:
                                self.ui.debug(f"Found plugin class: {plugin_name}")

                except Exception as e:
                    self.ui.error(f"Error loading plugin {plugin_dir.name}: {str(e)}")
                    continue

        except Exception as e:
            self.ui.error(f"Error during plugin discovery: {str(e)}")

        if self.debug:
            self.ui.debug(f"Plugin discovery completed. Found plugins: {list(plugins.keys())}")
        return plugins

    def get_plugin_path(self) -> Path:
        """Get the user plugins directory path"""
        return self.plugins_dir

    def create_plugin_template(self, plugin_name: str) -> None:
        """Create a new plugin template in the plugins directory"""
        plugin_dir = self.plugins_dir / plugin_name
        plugin_dir.mkdir(exist_ok=True)