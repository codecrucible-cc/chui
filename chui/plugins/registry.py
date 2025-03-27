# chui/plugins/registry.py

from typing import Dict, Type, Optional, List
from pathlib import Path
from datetime import datetime
from ..commands import BaseCommand
from .base import Plugin
from .discovery import PluginDiscovery
from ..events.base import Event, EventManager
from ..core.errors import PluginError, ErrorHandler, ErrorCategory
from ..protocols import CLIProtocol
from ..ui import UI
from ..config import Config


class PluginRegistry:
    """Unified plugin and command registry"""

    def __init__(self, ui: UI, config: Config, events: EventManager, error_handler: ErrorHandler, cli: CLIProtocol):
        self.ui = ui
        self.config = config
        self.events = events
        self.error_handler = error_handler
        self.cli = cli  # Store CLI reference
        self.debug = self.config.get('system.debug', False)

        # Explicitly log the plugin paths from config
        plugin_paths = self.config.get('plugins.paths', [])
        if self.debug:
            self.ui.debug(f"Plugin paths from config: {plugin_paths}")
            
            # Verify home directory is being properly resolved
            home_dir = str(Path.home())
            self.ui.debug(f"Home directory: {home_dir}")
            
            # If the path uses ~, show the expanded version
            if plugin_paths and isinstance(plugin_paths, list) and plugin_paths[0]:
                if plugin_paths[0].startswith('~'):
                    expanded = str(Path(plugin_paths[0]).expanduser())
                    self.ui.debug(f"Expanded plugin path: {expanded}")

        # Initialize discovery system with explicit parameters
        self.discovery = PluginDiscovery(ui=self.ui, config=self.config)

        # Log the actual plugin directory being used
        if self.debug:
            self.ui.debug(f"Actual plugin directory: {self.discovery.plugins_dir}")

        # Command pipeline reference from CLI
        self.command_pipeline = cli.command_pipeline

        # Storage
        self.plugins: Dict[str, Plugin] = {}
        self.commands: Dict[str, BaseCommand] = {}
        self._load_order: List[str] = []

        # Command category tracking
        self.command_categories: Dict[str, List[str]] = {
            'core': [],  # Built-in commands
            'plugin': [],  # Plugin-provided commands
            'admin': [],  # Administrative commands
        }

        # Load enabled plugins
        self._load_enabled_plugins()

    def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins from configuration"""
        try:
            if self.debug:
                self.ui.debug("Starting plugin loading process...")

            # Discover available plugins
            available_plugins = self.discovery.discover_plugins()
            if self.debug:
                self.ui.debug(f"Discovered plugins: {list(available_plugins.keys())}")

            # Get enabled/disabled lists
            enabled_plugins = self.config.get('plugins.enabled', [])
            disabled_plugins = self.config.get('plugins.disabled', [])
            auto_load = self.config.get('plugins.auto_load', True)

            if self.debug:
                self.ui.debug(f"Auto-load setting: {auto_load}")
                self.ui.debug(f"Enabled plugins: {enabled_plugins}")
                self.ui.debug(f"Disabled plugins: {disabled_plugins}")

            if auto_load:
                if self.debug:
                    self.ui.debug("Auto-loading plugins...")

                for plugin_name, plugin_class in available_plugins.items():
                    if plugin_name not in disabled_plugins:
                        if self.debug:
                            self.ui.debug(f"Attempting to load plugin: {plugin_name}")
                            self.ui.debug(f"Plugin class: {plugin_class}")

                        try:
                            self.load_plugin(plugin_class)
                            if self.debug:
                                self.ui.debug(f"Successfully loaded plugin: {plugin_name}")
                                plugin = self.plugins.get(plugin_name)
                                if plugin:
                                    commands = plugin.get_commands()
                                    self.ui.debug(f"Plugin commands: {list(commands.keys())}")
                        except Exception as e:
                            self.ui.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            else:
                if self.debug:
                    self.ui.debug("Loading only explicitly enabled plugins...")
                # Load only explicitly enabled plugins
                for plugin_name in enabled_plugins:
                    if plugin_name in available_plugins and plugin_name not in disabled_plugins:
                        if self.debug:
                            self.ui.debug(f"Loading enabled plugin: {plugin_name}")
                        self.load_plugin(available_plugins[plugin_name])

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.PLUGIN,
                operation="_load_enabled_plugins",
                debug=self.debug
            )

    def load_plugin(self, plugin_class: Type[Plugin]) -> None:
        """Load and initialize a plugin"""
        try:
            # Create plugin instance
            plugin = plugin_class(self.ui, self.config, self.events)

            if self.debug:
                self.ui.debug(f"Created plugin instance: {plugin.name}")

            # Validate plugin
            if not plugin.name:
                raise PluginError("Plugin must have a name")

            if plugin.name in self.plugins:
                raise PluginError(f"Plugin {plugin.name} is already loaded")

            # Check dependencies
            missing_deps = [dep for dep in plugin.dependencies
                            if dep not in self.plugins]
            if missing_deps:
                raise PluginError(
                    f"Missing dependencies for {plugin.name}: {', '.join(missing_deps)}"
                )

            # Initialize plugin
            plugin.initialize()

            # Register plugin
            self.plugins[plugin.name] = plugin
            self._load_order.append(plugin.name)

            # Register commands
            commands = plugin.get_commands()
            for cmd_name, cmd_class in commands.items():
                if self.debug:
                    self.ui.debug(f"Registering command: {cmd_name}")
                self.cli.register_plugin_command(cmd_name, cmd_class)

            # Emit plugin loaded event
            self.events.emit(Event(
                name="plugin_loaded",
                data={
                    "plugin_name": plugin.name,
                    "version": plugin.version
                },
                timestamp=datetime.now()
            ))

            if self.debug:
                self.ui.success(f"Successfully loaded plugin: {plugin.name} v{plugin.version}")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.PLUGIN,
                operation=f"load_plugin({plugin_class.__name__})",
                debug=self.debug
            )
            raise

    def register_command(self, name: str, command_instance: BaseCommand,
                         category: str = 'plugin') -> None:
        """Register a command instance"""
        try:
            if name in self.commands:
                raise PluginError(f"Command {name} is already registered")

            self.commands[name] = command_instance

            # Track command category
            if category not in self.command_categories:
                self.command_categories[category] = []
            self.command_categories[category].append(name)

            if self.debug:
                self.ui.debug(f"Registered command: {name} ({category})")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.PLUGIN,
                operation=f"register_command({name})",
                debug=self.debug
            )

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a command instance by name"""
        return self.commands.get(name)

    def get_available_plugins(self) -> Dict[str, str]:
        """Get all available plugins and their versions"""
        plugins = {}
        for name, plugin_class in self.discovery.discover_plugins().items():
            try:
                plugin = plugin_class(self.ui, self.config, self.events)
                plugins[name] = plugin.version
            except:
                plugins[name] = "unknown"
        return plugins

    def get_plugin_commands(self, plugin_name: str) -> List[str]:
        """Get all command names provided by a plugin"""
        if plugin_name not in self.plugins:
            return []
        return list(self.plugins[plugin_name].get_commands().keys())

    def get_commands_by_category(self, category: str) -> List[str]:
        """Get all command names in a category"""
        return self.command_categories.get(category, []).copy()

    def unload_plugin(self, name: str) -> None:
        """Unload a plugin and its commands"""
        try:
            if name not in self.plugins:
                raise PluginError(f"Plugin {name} is not loaded")

            plugin = self.plugins[name]

            # Check for dependent plugins
            dependents = [p.name for p in self.plugins.values()
                          if name in p.dependencies]
            if dependents:
                raise PluginError(
                    f"Cannot unload {name}, required by: {', '.join(dependents)}"
                )

            # Unregister commands
            for cmd_name in list(self.commands.keys()):
                if cmd_name in plugin.get_commands():
                    del self.commands[cmd_name]

                    # Remove from categories
                    for category in self.command_categories.values():
                        if cmd_name in category:
                            category.remove(cmd_name)

            # Cleanup plugin
            plugin.cleanup()

            # Remove plugin
            del self.plugins[name]
            self._load_order.remove(name)

            # Emit plugin unloaded event
            self.events.emit(Event(
                name="plugin_unloaded",
                data={
                    "plugin_name": name
                },
                timestamp=datetime.now()
            ))

            if self.debug:
                self.ui.debug(f"Unloaded plugin: {name}")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.PLUGIN,
                operation=f"unload_plugin({name})",
                debug=self.debug
            )

    def reload_plugin(self, name: str) -> None:
        """Reload a plugin"""
        if name not in self.plugins:
            raise PluginError(f"Plugin {name} is not loaded")

        plugin_class = type(self.plugins[name])
        self.unload_plugin(name)
        self.load_plugin(plugin_class)

    def cleanup(self) -> None:
        """Clean up all plugins"""
        for name in list(self.plugins.keys()):
            self.unload_plugin(name)
