# chui/plugins/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.errors import PluginError, ErrorCategory
from ..events.base import Event, EventManager
from ..config import Config
from ..ui import UI


class Plugin(ABC):
    """Base class for all Chui plugins

    This abstract class defines the interface that all plugins must implement.
    It provides core functionality for plugin lifecycle management, command registration,
    and event handling.

    Attributes:
        ui (UI): UI instance for user interaction
        config (Config): Config instance for plugin settings
        events (EventManager): Event manager for plugin events
        initialized (bool): Whether plugin has been initialized
        debug (bool): Whether debug mode is enabled
    """

    def __init__(self, ui: UI, config: Config, events: EventManager):
        """Initialize plugin with required components

        Args:
            ui: UI instance for user interaction
            config: Config instance for settings
            events: Event manager for plugin events
        """
        self.ui = ui
        self.config = config
        self.events = events
        self.initialized = False
        self.debug = config.get('system.debug', False)

        # Store initialization time
        self._init_time = datetime.now()

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name - must be unique across all plugins"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string (e.g. '1.0.0')"""
        pass

    @property
    def description(self) -> str:
        """Optional plugin description"""
        return ""

    @property
    def dependencies(self) -> List[str]:
        """List of required plugin names

        Returns:
            List of plugin names that must be loaded before this plugin
        """
        return []

    @property
    def initialized_time(self) -> Optional[datetime]:
        """Get the time when plugin was initialized

        Returns:
            Datetime when initialize() was called, or None if not initialized
        """
        return self._init_time if self.initialized else None

    def initialize(self) -> None:
        """Initialize the plugin

        This method is called after the plugin is loaded but before any commands
        are registered. Override to perform any required setup.

        Raises:
            PluginError: If initialization fails
        """
        try:
            if self.debug:
                self.ui.debug(f"Initializing plugin: {self.name}")

            # Perform initialization
            self._initialize()

            # Mark as initialized
            self.initialized = True
            self._init_time = datetime.now()

            if self.debug:
                self.ui.debug(f"Plugin {self.name} initialized successfully")

        except Exception as e:
            raise PluginError(f"Failed to initialize plugin {self.name}: {str(e)}")

    def _initialize(self) -> None:
        """Override this method to perform actual initialization

        This is where plugin-specific initialization should go. The base initialize()
        method handles the boilerplate.
        """
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources

        This method is called when the plugin is being unloaded. Override to perform
        any required cleanup.
        """
        try:
            if self.debug:
                self.ui.debug(f"Cleaning up plugin: {self.name}")

            # Perform cleanup
            self._cleanup()

            # Reset initialization flag
            self.initialized = False

            if self.debug:
                self.ui.debug(f"Plugin {self.name} cleaned up successfully")

        except Exception as e:
            self.ui.error(f"Error cleaning up plugin {self.name}: {str(e)}")

    def _cleanup(self) -> None:
        """Override this method to perform actual cleanup

        This is where plugin-specific cleanup should go. The base cleanup()
        method handles the boilerplate.
        """
        pass

    def get_commands(self) -> Dict[str, Any]:
        """Get plugin commands

        Returns:
            Dictionary mapping command names to command classes
        """
        return {}

    def get_hooks(self) -> Dict[str, Any]:
        """Get plugin event hooks

        Returns:
            Dictionary mapping event names to handler functions
        """
        return {}

    def emit_event(self, name: str, data: Any = None) -> None:
        """Emit a plugin-specific event

        Args:
            name: Event name
            data: Optional event data
        """
        try:
            self.events.emit(Event(
                name=f"{self.name}.{name}",
                data=data,
                timestamp=datetime.now()
            ))
        except Exception as e:
            if self.debug:
                self.ui.debug(f"Error emitting event {name}: {str(e)}")

    def __str__(self) -> str:
        """String representation of plugin"""
        return f"{self.name} v{self.version}"

    def __repr__(self) -> str:
        """Detailed string representation of plugin"""
        return (f"<Plugin '{self.name}' "
                f"v{self.version} "
                f"({'initialized' if self.initialized else 'not initialized'})>")