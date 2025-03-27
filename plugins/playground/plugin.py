from typing import Dict, List, Type
from chui.plugins.base import Plugin
from chui.commands import BaseCommand
from chui.protocols import CLIProtocol
from .commands import (
    PlaygroundCommand,
    DemoNamespacedCommand,
    TablesCommand,
    FormsCommand,
    PanelsCommand,
    PaginationCommand,
    ProgressCommand,
    ColorsCommand
)

class PlaygroundPlugin(Plugin):
    """
    Playground Plugin - Demonstrates CHUI Framework capabilities
    
    This plugin provides interactive demonstrations of various CHUI features
    including UI components, command handling, event systems, and more.
    """

    @property
    def name(self) -> str:
        return "playground"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Interactive playground and demos for CHUI Framework"

    @property
    def dependencies(self) -> List[str]:
        return []

    def _initialize(self) -> None:
        """Initialize plugin - called after loading"""
        if self.debug:
            self.ui.debug(f"Initializing {self.name} plugin")
            
        # Register for events
        self.events.subscribe("playground.demo_started", self._on_demo_started)
        self.events.subscribe("playground.demo_completed", self._on_demo_completed)

    def _cleanup(self) -> None:
        """Cleanup plugin resources - called before unloading"""
        if self.debug:
            self.ui.debug(f"Cleaning up {self.name} plugin")
            
        # Unregister from events
        try:
            self.events.unsubscribe("playground.demo_started", self._on_demo_started)
            self.events.unsubscribe("playground.demo_completed", self._on_demo_completed)
        except Exception as e:
            self.ui.debug(f"Error unsubscribing from events: {str(e)}")

    def get_commands(self) -> Dict[str, Type[BaseCommand]]:
        """Get plugin commands"""
        return {
            "playground": PlaygroundCommand,
            "demo": DemoNamespacedCommand,
            # Legacy commands removed
        }
        
    def _on_demo_started(self, event) -> None:
        """Handle demo started event"""
        if self.debug:
            self.ui.debug(f"Demo started: {event.data.get('demo', 'unknown')}")
            
    def _on_demo_completed(self, event) -> None:
        """Handle demo completed event"""
        if self.debug:
            self.ui.debug(f"Demo completed: {event.data.get('demo', 'unknown')}")


def setup(cli: CLIProtocol) -> None:
    """Register plugin with the CLI"""
    try:
        # Create and initialize plugin
        plugin = PlaygroundPlugin(cli.ui, cli.config, cli.events)
        plugin.initialize()

        # Register commands
        for cmd_name, cmd_class in plugin.get_commands().items():
            cli.register_plugin_command(cmd_name, cmd_class)

        if hasattr(cli, 'ui'):
            cli.ui.success(f"{plugin.name} plugin registered successfully")

    except Exception as e:
        if hasattr(cli, 'ui'):
            cli.ui.error(f"Failed to register {plugin.name} plugin: {str(e)}")
        raise