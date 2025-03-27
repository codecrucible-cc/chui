# chui/core/create_plugin.py

import os
import sys
from pathlib import Path
from typing import Optional
from textwrap import dedent


class PluginCreator:
    """Plugin creation utility for Chui framework"""

    def __init__(self):
        self.plugins_dir = Path.cwd() / 'plugins'

    def create(self, name: str, description: str = "", author: str = "") -> Path:
        """Create a new plugin from template"""
        # Sanitize plugin name
        plugin_name = name.lower().replace(' ', '_').replace('-', '_')
        plugin_dir = self.plugins_dir / plugin_name

        # Validate plugin name
        if not self._validate_plugin_name(plugin_name):
            raise ValueError(
                "Plugin name must be a valid Python identifier and not start with numbers"
            )

        # Create plugin structure
        self._ensure_plugins_dir()
        self._create_plugin_structure(plugin_name, plugin_dir, description, author)

        return plugin_dir

    def _validate_plugin_name(self, name: str) -> bool:
        """Validate plugin name is a valid Python identifier"""
        if not name.isidentifier():
            return False
        if name[0].isdigit():
            return False
        return True

    def _ensure_plugins_dir(self) -> None:
        """Ensure plugins directory exists"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True)
            (self.plugins_dir / '__init__.py').write_text(
                '"""Chui plugins directory"""\n'
            )

    def _create_plugin_structure(self, name: str, plugin_dir: Path,
                                 description: str, author: str) -> None:
        """Create the full plugin directory structure and files"""
        plugin_dir.mkdir(exist_ok=True)

        templates = {
            '__init__.py': self._get_init_template,
            'plugin.py': self._get_plugin_template,
            'commands.py': self._get_commands_template,
            'test_plugin.py': self._get_test_template,
            'README.md': self._get_readme_template
        }

        for filename, template_func in templates.items():
            content = template_func(name, description, author)
            (plugin_dir / filename).write_text(content)

    def _get_init_template(self, name: str, description: str, author: str) -> str:
        """Get the __init__.py template"""
        return dedent(f'''
            """
            {description}

            This plugin was created using Chui's plugin creation tool.
            """
            from .plugin import {name.title()}Plugin, setup

            __all__ = ['{name.title()}Plugin', 'setup']
        ''').lstrip()

    def _get_plugin_template(self, name: str, description: str, author: str) -> str:
        """Get the plugin.py template"""
        return dedent(f'''
            from typing import Dict, List, Type
            from chui.plugins.base import Plugin
            from chui.commands import BaseCommand
            from chui.protocols import CLIProtocol
            from .commands import {name.title()}Command

            class {name.title()}Plugin(Plugin):
                """
                {description}

                Author: {author}
                """

                @property
                def name(self) -> str:
                    return "{name}"

                @property
                def version(self) -> str:
                    return "0.1.0"

                @property
                def description(self) -> str:
                    return "{description}"

                @property
                def dependencies(self) -> List[str]:
                    return []

                def _initialize(self) -> None:
                    """Initialize plugin - called after loading"""
                    if self.debug:
                        self.ui.debug(f"Initializing {{self.name}} plugin")

                    # Add initialization code here
                    pass

                def _cleanup(self) -> None:
                    """Cleanup plugin resources - called before unloading"""
                    if self.debug:
                        self.ui.debug(f"Cleaning up {{self.name}} plugin")

                    # Add cleanup code here
                    pass

                def get_commands(self) -> Dict[str, Type[BaseCommand]]:
                    """Get plugin commands"""
                    return {{
                        "{name}": {name.title()}Command
                    }}

            def setup(cli: CLIProtocol) -> None:
                """Register plugin with the CLI"""
                try:
                    # Create and initialize plugin
                    plugin = {name.title()}Plugin(cli.ui, cli.config, cli.events)
                    plugin.initialize()

                    # Register commands
                    for cmd_name, cmd_class in plugin.get_commands().items():
                        cli.register_plugin_command(cmd_name, cmd_class)

                    if hasattr(cli, 'ui'):
                        cli.ui.debug(f"{{plugin.name}} plugin registered successfully")

                except Exception as e:
                    if hasattr(cli, 'ui'):
                        cli.ui.error(f"Failed to register {{plugin.name}} plugin: {{str(e)}}")
                    raise
        ''').lstrip()

    def _get_commands_template(self, name: str, description: str, author: str) -> str:
        """Get the commands.py template"""
        return dedent(f'''
            from typing import Any
            from chui.commands import BaseCommand, CommandContext

            class {name.title()}Command(BaseCommand):
                """Main command for {name} plugin"""

                @property
                def name(self) -> str:
                    return "{name}"

                def run(self, context: CommandContext) -> Any:
                    """Execute the command"""
                    # Get debug setting
                    debug = self.config.get('system.debug', False)

                    if debug:
                        self.ui.debug(f"Executing {name} command")
                        self.ui.debug(f"Args: {{context.args}}")
                        self.ui.debug(f"Flags: {{context.flags}}")
                        self.ui.debug(f"Options: {{context.options}}")

                    # Add your command logic here
                    self.ui.info("Hello from {name} plugin!")

                    # Show example of different message types
                    self.ui.success("This is a success message")
                    self.ui.warning("This is a warning message")
                    self.ui.error("This is an error message")

                    if debug:
                        self.ui.debug("This debug message only shows when debug is enabled")

                    return True

                def get_help(self) -> str:
                    """Get command help text"""
                    return """
                    {name} plugin command

                    Usage: {name} [options] [args...]

                    Options:
                        --help      Show this help message
                        --debug     Enable debug output

                    Examples:
                        {name}                  # Run default command
                        {name} --help           # Show help
                        {name} arg1 arg2        # Pass arguments
                        {name} --debug          # Enable debug output
                    """

            # Example of a namespaced command (uncomment and modify as needed):
            # class {name.title()}NamespacedCommand(BaseCommand):
            #     """Command with subcommands"""
            #
            #     @property
            #     def name(self) -> str:
            #         return "{name}ns"
            #     
            #     @property
            #     def namespace(self) -> str:
            #         return "{name}"
            #
            #     def __init__(self, ui, config, pipeline=None):
            #         super().__init__(ui, config, pipeline)
            #         # Register subcommands
            #         self.register_subcommand("list", self.cmd_list, "List items")
            #         self.register_subcommand("add", self.cmd_add, "Add an item")
            #         self.register_alias("ls", "list")  # Optional alias
            #
            #     def cmd_list(self, context: CommandContext) -> Any:
            #         self.ui.info("Listing items...")
            #         return True
            #
            #     def cmd_add(self, context: CommandContext) -> Any:
            #         if not context.args:
            #             self.ui.error("Item name required")
            #             return False
            #         self.ui.success(f"Adding item: {{context.args[0]}}")
            #         return True
        ''').lstrip()

    def _get_test_template(self, name: str, description: str, author: str) -> str:
        """Get the test_plugin.py template"""
        return dedent(f'''
            import pytest
            from chui.ui import UI
            from chui.config import Config
            from chui.events.base import EventManager
            from chui.core.errors import PluginError
            from chui.commands import CommandContext
            from .plugin import {name.title()}Plugin
            from .commands import {name.title()}Command

            @pytest.fixture
            def plugin(mocker):
                """Create a mock plugin instance"""
                ui = mocker.Mock(spec=UI)
                config = mocker.Mock(spec=Config)
                events = mocker.Mock(spec=EventManager)
                return {name.title()}Plugin(ui, config, events)

            @pytest.fixture
            def command(mocker):
                """Create a mock command instance"""
                ui = mocker.Mock(spec=UI)
                config = mocker.Mock(spec=Config)
                return {name.title()}Command(ui, config)

            @pytest.fixture
            def context():
                """Create a test command context"""
                return CommandContext(
                    name="{name}",
                    namespace=None,
                    args=[],
                    flags={{}},
                    options={{}},
                    original_input="",
                    timestamp=None,
                    metadata={{}}
                )

            class Test{name.title()}Plugin:
                """Test plugin functionality"""

                def test_plugin_properties(self, plugin):
                    """Test basic plugin properties"""
                    assert plugin.name == "{name}"
                    assert isinstance(plugin.version, str)
                    assert isinstance(plugin.description, str)
                    assert isinstance(plugin.dependencies, list)

                def test_plugin_commands(self, plugin):
                    """Test plugin command registration"""
                    commands = plugin.get_commands()
                    assert isinstance(commands, dict)
                    assert "{name}" in commands
                    assert commands["{name}"] == {name.title()}Command

            class Test{name.title()}Command:
                """Test command functionality"""

                def test_command_help(self, command):
                    """Test command help text"""
                    help_text = command.get_help()
                    assert isinstance(help_text, str)
                    assert len(help_text) > 0

                def test_command_execution(self, command, context):
                    """Test basic command execution"""
                    result = command.run(context)
                    assert result is True
                    command.ui.info.assert_called()

                def test_command_with_args(self, command, context):
                    """Test command with arguments"""
                    context.args = ["test_arg"]
                    result = command.run(context)
                    assert result is True

                def test_command_with_debug(self, command, context):
                    """Test command with debug flag"""
                    command.config.get.return_value = True  # Enable debug
                    result = command.run(context)
                    assert result is True
                    command.ui.debug.assert_called()
        ''').lstrip()

    def _get_readme_template(self, name: str, description: str, author: str) -> str:
        """Get the README.md template"""
        return dedent(f'''
            # {name.title()} Plugin for Chui Framework

            {description}

            ## Author
            {author}

            ## Installation

            1. Ensure this plugin directory is in your Chui plugins directory
            2. Enable the plugin in Chui's configuration:
               ```python
               config.set("plugins.enabled", ["{name}"])
               ```

            ## Usage

            ```bash
            # Show help
            chui> {name} --help

            # Run default command
            chui> {name}

            # Pass arguments
            chui> {name} arg1 arg2
            ```

            ## Development

            ### Running Tests
            ```bash
            pytest plugins/{name}/test_plugin.py
            ```

            ### Debug Mode
            Enable debug output:
            ```python
            config.set("system.debug", True)
            ```

            ## License
            Add your license information here.
        ''').lstrip()