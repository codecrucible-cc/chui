# chui/protocols.py

from typing import Protocol, Type, runtime_checkable
from .commands import BaseCommand


@runtime_checkable
class CLIProtocol(Protocol):
    """Protocol defining CLI interface for plugins"""

    def register_plugin_command(self, name: str, command_class: Type[BaseCommand]) -> None:
        """Register a plugin command"""
        ...

    def get_command(self, name: str) -> BaseCommand:
        """Get a registered command"""
        ...

    def unregister_command(self, name: str) -> None:
        """Unregister a command"""
        ...


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol defining plugin interface"""

    @property
    def name(self) -> str:
        """Plugin name"""
        ...

    @property
    def version(self) -> str:
        """Plugin version"""
        ...

    def get_commands(self) -> dict:
        """Get plugin commands"""
        ...
