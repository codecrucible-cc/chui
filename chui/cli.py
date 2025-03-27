# chui/cli.py

import cmd2
import os
import time
import platform
from typing import Dict, List, Optional, Type, Callable

from chui.ui import UI
from .config import Config
from chui.plugins.registry import PluginRegistry
from .commands import BaseCommand
from .protocols import CLIProtocol
from chui.events.base import EventManager
from chui.core.errors import ErrorHandler, CommandError, ErrorCategory, ErrorSeverity
from .core.cli_utils import CLIUtils
from .commands.pipeline import CommandPipeline
from .commands.registry import CommandRegistry

class ChuiCLI(cmd2.Cmd, CLIProtocol):
    """Main CLI application class"""
    
    def __init__(self):
        # Initialize cmd2 with basic settings
        super().__init__(
            multiline_commands=['echo'],
            persistent_history_file='~/.chui/history'
        )

        self.debug = True  # Set to True temporarily for debugging
        self.show_banner = True

        self.utils = CLIUtils()

        # Initialize components
        self.ui = UI(cmd=self)
        self.ui.debug("UI initialized")

        self.config = Config("chui")
        self.config.init_ui(self.ui)
        self.ui.debug("Config initialized")

        self.events = EventManager()
        self.ui.debug("Event Manager initialized")

        self.error_handler = ErrorHandler(self.ui)
        self.ui.debug("Error Handler initialized")

        # Initialize command pipeline and registry before plugins
        self.command_pipeline = CommandPipeline(self.events, self.error_handler)
        self.ui.debug("Command Pipeline initialized")

        self.command_registry = CommandRegistry()
        self.ui.debug("Command Registry initialized")

        # Dictionary to store plugin command instances
        self._plugin_commands = {}

        # Add debug before plugin registry initialization
        self.ui.debug("Initializing Plugin Registry...")

        # Pass self (CLI instance) to PluginRegistry
        self.plugins = PluginRegistry(
            ui=self.ui,
            config=self.config,
            events=self.events,
            error_handler=self.error_handler,
            cli=self  # Pass CLI instance
        )
        self.ui.debug("Plugin Registry initialized")

        # Set basic properties
        self.prompt = 'chui> '
        self.intro = self._get_intro()

    def setup_event_handlers(self) -> None:
        """Setup CLI event handlers"""
        def on_plugin_loaded(event):
            self.ui.success(f"Plugin loaded: {event.data['plugin_name']} v{event.data['version']}")
            
        def on_plugin_unloaded(event):
            self.ui.info(f"Plugin unloaded: {event.data['plugin_name']}")
            
        self.events.subscribe('plugin_loaded', on_plugin_loaded)
        self.events.subscribe('plugin_unloaded', on_plugin_unloaded)
    
    def _get_intro(self) -> str:
        """Get the introduction banner"""
        return """
╔═════════════════════════════════════════════╗
║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║
║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║
║▒▒▒▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒▒▒▒▒▒▒▒║
║▒▒▒▒▒▒    ▒   ▒▒▒▒▒▒   ▒▒   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒║
║▓▓▓▓   ▓▓▓▓     ▓▓▓▓   ▓▓   ▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓║
║▓▓▓   ▓▓▓▓▓   ▓▓  ▓▓   ▓▓   ▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓║
║▓▓▓▓   ▓▓▓▓  ▓▓▓   ▓   ▓▓   ▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓║
║██████    █  ███   ███      █   █████████████║
║█████████████████████████████████████████████║
║                                             ║
║               Welcome to Chui               ║
║     CLI Hub & UI Interface Framework        ║
║                                             ║
╚═════════════════════════════════════════════╝
        """
    
    def clear_screen(self, initial: bool = False) -> None:
        """Clear the terminal screen and optionally show the banner"""
        # Clear screen based on OS
        os.system('cls' if os.name == 'nt' else 'clear')
        # Show banner if not initial setup
        if not initial and self.show_banner:
            self._display_banner()

    def _display_banner(self) -> None:
        """Display the CLI banner with session-related info"""
        # Gather session information
        os_name = platform.system()
        user_name = os.environ.get('USER') or os.environ.get('USERNAME') or 'Unknown User'
        log_level = self.config.get('system', {}).get('log_level', 'INFO')
        
        # Display the banner
        if self.show_banner:
            self.ui.panel(f"""
    Session Information:
    ---------------------
    Operating System: {os_name}
    User: {user_name}
    Log Level: {log_level}
            """, style="bold blue")
    
    def do_clear(self, _) -> None:
        """Clear the terminal screen"""
        self.clear_screen()

    def _complete_settings_path(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Tab completion for settings paths"""
        # If we're completing the command itself
        if line.strip() == 'settings':
            return ['edit', 'set', 'show']
            
        # Get the command part (edit/set/show)
        parts = line[:begidx].strip().split()
        if len(parts) < 2 or parts[1] not in ['edit', 'set', 'show']:
            return []
            
        cmd = parts[1]
        current = text.strip()
        
        # Debug logging if enabled
        if self.debug:
            self.ui.debug(f"Complete settings - text: '{text}' line: '{line}' current: '{current}'")
            self.ui.debug(f"Parts: {parts}, Command: {cmd}")
        
        # If we're at a section level
        if '.' not in current:
            matches = [
                section for section in self.config._config.keys()
                if section.startswith(current)
            ]
            if len(matches) == 1:
                # If exact match, add the dot
                if matches[0] == current:
                    return [f"{matches[0]}."]
                # Otherwise just return the match
                return matches
            return matches
        
        # Handle completion after dot
        if current.endswith('.'):
            section = current[:-1]
            if section in self.config._config:
                return [
                    f"{section}.{key}" 
                    for key in self.config._config[section].keys()
                    if isinstance(self.config._config[section][key], (str, bool, int, float, dict, list))
                ]
            return []
        
        # Completing setting name
        section, setting = current.rsplit('.', 1)
        if section not in self.config._config:
            return []
            
        # Get available settings for section
        settings = [
            key for key, value in self.config._config[section].items()
            if isinstance(value, (str, bool, int, float, dict, list))
            and key.startswith(setting)
        ]
        
        # Return matches with full path
        matches = [f"{section}.{s}" for s in settings]
        
        # Add space only for exact matches
        if len(matches) == 1 and matches[0] == current:
            return [f"{matches[0]} "]
            
        return matches

    def register_plugin_command(self, name: str, command_class: Type[BaseCommand]) -> None:
        """Register a plugin command"""
        try:
            # Create command instance with pipeline
            command_instance = command_class(
                self.ui,
                self.config,
                pipeline=self.command_pipeline
            )

            # Register command in registry with instance
            self.command_registry.register(
                name=name, 
                command_class=command_class,
                category='plugin',
                instance=command_instance
            )

            # Create the do_ and help_ methods
            def do_command(self_cmd, statement: str = '') -> bool:
                try:
                    parsed = self.utils.parse_command(statement)
                    if self.debug:
                        self.ui.debug(f"Executing {name} with args: {parsed.args}")

                    # Pass all args to execute
                    command_instance.execute(
                        parsed.args,
                        parsed.flags,
                        parsed.options,
                        statement  # Pass original input
                    )
                    return False  # Stay in CLI
                except Exception as e:
                    self.error_handler.handle(
                        error=e,
                        category=ErrorCategory.COMMAND,
                        severity=ErrorSeverity.ERROR,
                        operation=f"execute_command({name})",
                        debug=self.debug
                    )
                    return False

            def help_command(self):
                command_instance.show_help()

            # Add methods to class
            setattr(ChuiCLI, f'do_{name}', do_command)
            setattr(ChuiCLI, f'help_{name}', help_command)

            # Store command instance
            self._plugin_commands[name] = command_instance

            if self.debug:
                self.ui.debug(f"Registered command: {name}")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.PLUGIN,
                severity=ErrorSeverity.ERROR,
                operation=f"register_command({name})",
                debug=self.debug
            )
            raise
    
    def do_plugins(self, arg: str) -> None:
        """
        Manage plugins
        
        Usage:
          plugins list              List all plugins
          plugins load <name>       Load a plugin
          plugins unload <name>     Unload a plugin
          plugins reload <name>     Reload a plugin
          plugins info <name>       Show plugin details
        """
        try:
            args = arg.split()
            if not args:
                args = ['list']
            
            cmd = args[0].lower()
            
            if cmd == 'list':
                if not self.plugins.plugins:
                    self.ui.warning("No plugins loaded")
                    return
                    
                # Show plugins table
                headers = ["Name", "Version", "Commands", "Dependencies"]
                rows = []
                for name, plugin in self.plugins.plugins.items():
                    rows.append([
                        name,
                        plugin.version,
                        ", ".join(self.plugins.get_plugin_commands(name)),
                        ", ".join(plugin.dependencies) or "none"
                    ])
                self.ui.table(headers, rows, "Loaded Plugins")
                
            elif cmd == 'load' and len(args) > 1:
                self.plugins.load_plugin(args[1])
                
            elif cmd == 'unload' and len(args) > 1:
                self.plugins.unload_plugin(args[1])
                
            elif cmd == 'reload' and len(args) > 1:
                self.plugins.reload_plugin(args[1])
                
            elif cmd == 'info' and len(args) > 1:
                name = args[1]
                plugin = self.plugins.plugins.get(name)
                if not plugin:
                    self.ui.error(f"Plugin not found: {name}")
                    return
                    
                # Show plugin details
                self.ui.panel(f"""
                Plugin: {name}
                Version: {plugin.version}
                Commands: {', '.join(self.plugins.get_plugin_commands(name))}
                Dependencies: {', '.join(plugin.dependencies) or 'none'}
                """, title=f"Plugin Information: {name}")
                
            else:
                self.ui.error("Invalid command. Use 'help plugins' for usage.")
                
        except Exception as e:
            self.error_handler.handle(e, self.debug)


    def complete_settings(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Enable tab completion for settings command"""
        completions = self._complete_settings_path(text, line, begidx, endidx)
        
        # Debug output if needed
        if self.debug:
            self.ui.debug(f"Settings completion:")
            self.ui.debug(f"  text: '{text}'")
            self.ui.debug(f"  line: '{line}'")
            self.ui.debug(f"  completions: {completions}")
        
        return completions
    
    def _get_setting_components(self, setting_path: str) -> tuple[str, Optional[str]]:
        """Split a setting path into section and key components
        
        Args:
            setting_path: The full setting path (e.g. 'ui.theme')
            
        Returns:
            Tuple of (section, key) where key may be None for section-only paths
        """
        parts = setting_path.strip().split('.')
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1]

    def _get_completion_options(self, section: str, prefix: str = '') -> List[str]:
        """Get completion options for a section with optional prefix
        
        Args:
            section: The config section to look in
            prefix: Optional prefix to filter settings
            
        Returns:
            List of valid completion options
        """
        if section not in self.config._config:
            return []
            
        return [
            key for key in self.config._config[section].keys()
            if isinstance(self.config._config[section][key], (str, bool, int, float))
            and key.startswith(prefix)
        ]

    def do_settings(self, arg: str) -> None:
        """
        Show or modify CLI settings

        Usage:
            settings                   Show all settings
            settings edit SECTION.KEY  Edit specific setting
            settings set SECTION.KEY VALUE
                                    Set setting value
            settings debug            Show debug flags and system info
            settings reset SECTION    Reset a section to defaults
            settings reset_all        Reset all settings to defaults
            settings reset_all --plugins  Reset all settings including plugins

        Examples:
            settings edit ui.theme    Edit the UI theme
            settings set ui.theme dark
            settings show            Show all settings
            settings debug           Show system information
            settings reset ui        Reset UI settings to defaults
            settings reset_all       Reset all settings (preserves plugins)
        """
        args = arg.split()
        if not args:
            self.config.settings_ui.show_settings()
            return

        cmd = args[0].lower()

        if cmd == 'reset':
            if len(args) < 2:
                self.ui.error("Must specify section to reset")
                return
            self._handle_reset_section(args[1])
            return

        if cmd == 'reset_all':
            include_plugins = '--plugins' in args
            self._handle_reset_all(include_plugins)
            return

        if cmd == 'debug':
            self._show_debug_flags()
            return

        if cmd == 'edit' and len(args) > 1:
            section, key = self._get_setting_components(args[1])
            if not key:
                self.ui.error("Invalid setting path. Use format: section.key")
                return
            if self.config.is_debug_flag(f"{section}.{key}"):
                self.ui.error("Cannot edit debug flags - they are read-only system values")
                return
            self.config.settings_ui.edit_setting(f"{section}.{key}")

        elif cmd == 'set' and len(args) > 2:
            section, key = self._get_setting_components(args[1])
            if not key:
                self.ui.error("Invalid setting path. Use format: section.key")
                return
            if self.config.is_debug_flag(f"{section}.{key}"):
                self.ui.error("Cannot modify debug flags - they are read-only system values")
                return
            new_value = ' '.join(args[2:])
            self.config.settings_ui.update_setting(f"{section}.{key}", new_value)

        else:
            self.ui.error("Invalid command. Use 'help settings' for usage.")

    def _handle_reset_section(self, section: str) -> None:
        """Handle resetting a configuration section"""
        try:
            # Show what will be reset
            self.ui.warning(f"This will reset the following section to defaults: {section}")

            # Get current section settings for display
            current_settings = self.config._config.get(section, {})
            if current_settings:
                self.ui.info("\nCurrent settings that will be reset:")
                headers = ["Setting", "Current Value"]
                rows = [[k, str(v)] for k, v in current_settings.items()]
                self.ui.table(headers, rows)

            # Confirm with user
            if not self.ui.confirm("\nAre you sure you want to reset this section?", default=False):
                self.ui.info("Reset cancelled")
                return

            # Perform reset
            self.config.reset_section(section)
            self.ui.success(f"Successfully reset {section} configuration to defaults")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.CONFIG,
                severity=ErrorSeverity.ERROR,
                operation="reset_section",
                debug=self.debug
            )

    def _handle_reset_all(self, include_plugins: bool = False) -> None:
        """Handle resetting all configuration"""
        try:
            self.ui.warning("\nThis will reset ALL settings to their default values!")

            if include_plugins:
                # Show plugin configs that will be reset
                plugin_paths = self.config.get_plugin_config_paths()
                if plugin_paths:
                    self.ui.warning("\nThe following plugin configurations will also be reset:")
                    for path in plugin_paths:
                        self.ui.info(f"  - {path}")
            else:
                self.ui.info("\nPlugin configurations will be preserved")

            # Show current custom settings
            custom_settings = []
            default_config = self.config._get_dynamic_config()
            for section, settings in self.config._config.items():
                if section == 'debug':
                    continue
                if section not in default_config or isinstance(settings, dict):
                    for key, value in settings.items():
                        default_value = default_config.get(section, {}).get(key)
                        if value != default_value:
                            custom_settings.append([f"{section}.{key}", str(value)])

            if custom_settings:
                self.ui.info("\nCurrent custom settings that will be reset:")
                headers = ["Setting", "Current Value"]
                self.ui.table(headers, custom_settings)

            # Double-check with user
            message = "\nAre you sure you want to reset ALL settings to defaults?"
            if include_plugins:
                message += " This includes plugin configurations!"

            if not self.ui.confirm(message, default=False):
                self.ui.info("Reset cancelled")
                return

            # Perform reset
            self.config.reset_all(include_plugins)
            self.ui.success("Successfully reset all configurations to defaults")

            if include_plugins:
                self.ui.info("Plugin configurations have also been reset")
            else:
                self.ui.info("Plugin configurations have been preserved")

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.CONFIG,
                severity=ErrorSeverity.ERROR,
                operation="reset_all",
                debug=self.debug
            )
    def _show_debug_flags(self) -> None:
        """Display debug flags and system information"""
        debug_config = self.config._config.get('debug', {})

        # System Information
        self.ui.panel("System Information", style="bold blue")
        system_info = debug_config.get('system', {})
        headers = ["Property", "Value"]
        rows = [[k, str(v)] for k, v in system_info.items()]
        self.ui.table(headers, rows)

        # Terminal Information
        self.ui.panel("\nTerminal Information", style="bold green")
        terminal_info = debug_config.get('terminal', {})
        rows = [[k, str(v)] for k, v in terminal_info.items()]
        self.ui.table(headers, rows)

        # Network Information
        self.ui.panel("\nNetwork Information", style="bold yellow")
        network_info = debug_config.get('network', {})
        rows = [[k, str(v)] for k, v in network_info.items()]
        self.ui.table(headers, rows)

    def execute_command(self, line: str) -> None:
        """Execute a command with proper error handling"""
        try:
            # Parse command
            parsed = self.utils.parse_command(line)

            if not parsed.command:  # Handle empty command
                return

            # Get command instance
            command = self.get_command(parsed.command)
            if not command:
                raise CommandError(f"Unknown command: {parsed.command}")

            # Execute command
            command.execute(parsed.args, parsed.flags, parsed.options)

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.COMMAND,
                severity=ErrorSeverity.ERROR,
                operation="execute_command",
                debug=self.debug
            )

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a registered command"""
        return self._plugin_commands.get(name)
    
    def unregister_command(self, name: str) -> None:
        """Unregister a command"""
        if name in self._plugin_commands:
            delattr(ChuiCLI, f'do_{name}')
            delattr(ChuiCLI, f'help_{name}')
            del self._plugin_commands[name]
            
            if self.debug:
                self.ui.debug(f"Unregistered command: {name}")

    def default(self, line: str) -> None:
        """Handle unknown commands and special actions"""
        try:
            # Handle settings links
            if line.startswith(("edit:", "default:")):
                action, setting_key = line.split(":", 1)
                if action == "edit":
                    self.config.settings_ui.edit_setting(setting_key)
                else:  # default
                    self.config.settings_ui.set_to_default(setting_key)
                return

            # Try command execution
            self.execute_command(line)

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.COMMAND,
                severity=ErrorSeverity.ERROR,
                operation="default_handler",
                debug=self.debug
            )

        return super().default(line)
    

    def do_quit(self, _) -> bool:
        """Exit the CLI"""
        self.ui.info("Quitting...")
        self.ui.success("Goodbye! 👋")
        time.sleep(.33)
        self.clear_screen(initial=True)
        
        # Run cleanup
        self.plugins.cleanup()
        
        return True
    
    def cleanup(self) -> None:
        """Cleanup all components"""
        self.plugins.cleanup()
        # Add any other cleanup here
        
