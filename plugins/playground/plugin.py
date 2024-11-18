# plugins/playground/plugin.py

from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from rich.table import Table
from rich.markdown import Markdown

from chui.commands import BaseCommand, InfrastructureCommand
from chui.plugins.base import Plugin
from chui.protocols import CLIProtocol
from chui.ui import UI
from chui.config import Config
from chui.events.base import Event, EventManager
from chui.core.errors import (
    ConfigError,
    PluginError,
    CommandError,
    SecurityError,
    ErrorCategory,
    ErrorSeverity
)


class PlaygroundCommand(BaseCommand):
    def __init__(self, ui: UI, config: Config, pipeline=None):
        super().__init__(ui, config, pipeline)
        self.debug = config.get('system.debug', False)
        # Get events from UI to ensure we have access
        self.events = getattr(ui, 'cmd').events if hasattr(ui, 'cmd') else None
        self.error_handler = getattr(ui, 'cmd').error_handler if hasattr(ui, 'cmd') else None
        self.demos = {
            'ui': self._demo_ui,
            'config': self._demo_config,
            'events': self._demo_events,
            'pipeline': self._demo_pipeline,
            'error': self._demo_error_handling,
            'all': self._demo_all
        }

    def create_plugin(self) -> bool:
        """Demo creating a new plugin"""
        plugin_name = self.ui.prompt("Enter the name for your new plugin:")
        if not plugin_name:
            self.ui.error("Plugin name cannot be empty")
            return False

        try:
            self.discovery.create_plugin_template(plugin_name)
            self.ui.success(f"Created plugin template: {plugin_name}")
            self.ui.info(f"Plugin location: {self.discovery.get_plugin_path() / plugin_name}")
            return True
        except Exception as e:
            self.ui.error(f"Failed to create plugin: {str(e)}")
            return False

    def execute(self, args: List[str], flags: Dict[str, bool], options: Dict[str, str]) -> Any:
        """Execute the playground command"""
        if flags.get('help'):
            self.ui.info(self.help)
            return True

        # Handle demo selection
        if not args:
            # Interactive mode
            return self._interactive_demo()

        # Direct demo execution
        demo_name = args[0].lower()
        if demo_name in self.demos:
            return self.demos[demo_name]()
        else:
            self.ui.error(f"Unknown demo: {demo_name}")
            self.ui.info("Available demos: " + ", ".join(self.demos.keys()))
            return False

    def _interactive_demo(self) -> bool:
        """Run interactive demo selection"""
        demos = {
            "UI Components": self._demo_ui,
            "Configuration": self._demo_config,
            "Event System": self._demo_events,
            "Command Pipeline": self._demo_pipeline,
            "Error Handling": self._demo_error_handling,
            "Complete Demo": self._demo_all
        }

        self.ui.panel("""
🎮 Welcome to the Chui Framework Playground! 

This playground demonstrates various features and capabilities of the framework.
Choose a demo to explore different aspects of the framework.
        """, title="Chui Playground", style="bold blue")

        while True:
            # Create list of demo options with descriptions
            options = []
            for name, func in demos.items():
                doc = func.__doc__.split('\n')[0] if func.__doc__ else ''
                options.append(f"{name} - {doc}")
            options.append("Exit Playground - Return to main CLI")

            # Use UI's select_from_list method
            selection = self.ui.select_from_list(options, "Select a demo to run:")

            # Extract demo name from selection
            demo_name = selection.split(" - ")[0]

            # Check for exit
            if demo_name == "Exit Playground":
                return True

            # Execute selected demo
            try:
                demo_func = demos[demo_name]
                result = demo_func()

                if not result:
                    self.ui.warning("Demo completed with warnings or errors")

                # Ask about continuing
                if not self.ui.confirm("Would you like to try another demo?"):
                    return True

            except Exception as e:
                self.ui.error("Error running demo: " + str(e))
                if self.debug:
                    import traceback
                    self.ui.debug("Traceback:\n" + traceback.format_exc())

                if not self.ui.confirm("Would you like to try another demo?"):
                    return True

        return True

    def _demo_ui(self) -> bool:
        """Demonstrates UI components and interactive features"""
        self.ui.panel("UI Components Demonstration", style="bold green")

        # Basic message types
        self.ui.info("This is an info message")
        self.ui.success("This is a success message")
        self.ui.warning("This is a warning message")
        self.ui.error("This is an error message")
        self.ui.debug("This is a debug message")

        # Interactive prompts
        if self.ui.confirm("Would you like to see interactive prompts?"):
            name = self.ui.prompt("What's your name?")
            self.ui.success(f"Hello, {name}!")

            # Selection
            colors = ["Red", "Blue", "Green", "Yellow"]
            color = self.ui.select_from_list(colors, "Select your favorite color:")
            self.ui.success(f"You selected: {color}")

        # Tables
        self.ui.info("\nDemonstrating tables:")
        headers = ["Feature", "Description", "Status"]
        rows = [
            ["UI Messages", "Different message types", "✓"],
            ["Interactive", "User input handling", "✓"],
            ["Tables", "Formatted data display", "✓"],
            ["Links", "Clickable links", "✓"]
        ]
        self.ui.table(headers, rows, "Framework Features")

        # Links
        self.ui.info("\nDemonstrating links:")
        self.ui.link("Chui Documentation", "https://docs.example.com/chui")

        links = [
            {"url": "https://example.com/docs", "description": "Documentation"},
            {"url": "https://example.com/guide", "description": "User Guide"}
        ]
        self.ui.link_list(links, "Useful Resources")

        # Panels
        self.ui.panel("""
        Panels can be used to display:
        • Important information
        • Grouped content
        • Highlighted sections
        """, title="About Panels", style="bold blue")

        return True

    def _demo_config(self) -> bool:
        """Demonstrates configuration management and storage"""
        self.ui.panel("Configuration Management Demonstration", style="bold magenta")

        # Show current config
        self.ui.info("Current playground configuration:")
        playground_config = {
            "last_run": self.config.get("playground.last_run", "Never"),
            "run_count": self.config.get("playground.run_count", 0),
            "favorite_color": self.config.get("playground.favorite_color", "None set")
        }

        headers = ["Setting", "Value"]
        rows = [[k, str(v)] for k, v in playground_config.items()]
        self.ui.table(headers, rows, "Playground Settings")

        # Update configuration
        if self.ui.confirm("Would you like to update the configuration?"):
            color = self.ui.prompt("Enter your favorite color:")
            self.config.set("playground.favorite_color", color)

            # Update run statistics
            run_count = self.config.get("playground.run_count", 0) + 1
            self.config.set("playground.run_count", run_count)
            self.config.set("playground.last_run", datetime.now().isoformat())

            self.ui.success("Configuration updated!")

            # Show updated config
            self.ui.info("\nUpdated configuration:")
            playground_config = {
                "last_run": self.config.get("playground.last_run"),
                "run_count": self.config.get("playground.run_count"),
                "favorite_color": self.config.get("playground.favorite_color")
            }
            rows = [[k, str(v)] for k, v in playground_config.items()]
            self.ui.table(headers, rows, "Updated Settings")

        # Demonstrate encryption
        if self.ui.confirm("\nWould you like to see secure configuration storage?"):
            encryption_mgr = self.config.get_encrypted_manager()

            # Store encrypted value
            secret = self.ui.prompt("Enter a secret value to encrypt:")
            encryption_mgr.set_encrypted("playground.secret", secret)

            # Retrieve and show encrypted value
            decrypted = encryption_mgr.get_decrypted("playground.secret")
            self.ui.success(f"Successfully stored and retrieved encrypted value: {decrypted}")

        return True

    def _demo_events(self) -> bool:
        """Demonstrates event system and handling capabilities"""
        self.ui.panel("Event System Demonstration", style="bold yellow")

        def on_test_event(event: Event):
            self.ui.info(f"Event received: {event.name}")
            self.ui.info(f"Event data: {event.data}")

        # Register event handler
        self.events.subscribe("playground.test", on_test_event)

        # Emit test events
        self.ui.info("Emitting test events...")

        # Start operation
        operation_id = self.events.start_operation("playground_demo")

        # Emit various events
        events = [
            ("playground.test", {"message": "Hello from playground!"}),
            ("playground.test", {"message": "Testing events...", "count": 1}),
            ("playground.test", {"message": "Final test event", "status": "complete"})
        ]

        for event_name, event_data in events:
            self.events.emit(Event(
                name=event_name,
                data=event_data,
                timestamp=datetime.now(),
                operation_id=operation_id
            ))

        # Complete operation
        self.events.complete_operation(operation_id)

        # Show operation timeline
        timeline = self.events.get_operation_timeline(operation_id)

        self.ui.info("\nOperation Timeline:")
        headers = ["Timestamp", "Event", "Data"]
        rows = [
            [
                event["timestamp"].strftime("%H:%M:%S"),
                event["name"],
                str(event["data"])
            ]
            for event in timeline
        ]
        self.ui.table(headers, rows, "Event Timeline")

        return True

    def _demo_pipeline(self) -> bool:
        """Demonstrates command pipeline and execution flow"""
        self.ui.panel("Command Pipeline Demonstration", style="bold cyan")

        if not self.pipeline:
            self.ui.warning("Command pipeline not available. Some features will be limited.")
            return False

        # Create a test command context
        from uuid import uuid4
        from chui.commands.pipeline import CommandContext

        context = CommandContext(
            command_id=uuid4(),
            name="playground_test",
            args=["test"],
            options={"test": "value"},
            env={"PLAYGROUND": "true"}
        )

        # Execute through pipeline
        self.ui.info("Executing test command through pipeline...")
        result = self.pipeline.execute(context)

        # Show results
        headers = ["Property", "Value"]
        rows = [
            ["Command ID", str(result.command_id)],
            ["Status", str(result.status)],
            ["Start Time", str(result.start_time)],
            ["End Time", str(result.end_time)],
            ["Exit Code", str(result.exit_code)],
            ["Output", str(result.output)],
            ["Error", str(result.error)]
        ]
        self.ui.table(headers, rows, "Pipeline Execution Results")

        return True

    def _demo_error_handling(self) -> bool:
        """Demonstrates error handling and recovery mechanisms"""
        self.ui.panel("Error Handling Demonstration", style="bold red")

        if not self.error_handler:
            self.ui.error("Error handler not available")
            return False

        def trigger_error(error_type: str):
            if error_type == "config":
                raise ConfigError(
                    "Test configuration error",
                    severity=ErrorSeverity.WARNING,
                    context={'setting': 'test.setting'}
                )
            elif error_type == "plugin":
                raise PluginError(
                    "Test plugin error",
                    plugin_name="playground"
                )
            elif error_type == "command":
                raise CommandError(
                    "Test command error",
                    command="playground",
                    args=["test"]
                )
            elif error_type == "security":
                raise SecurityError(
                    message="Test security error",
                    violation_type=SecurityError.ViolationType.UNAUTHORIZED_ACCESS,
                    operation="test",
                    user="playground",
                    severity=ErrorSeverity.WARNING
                )
            else:
                raise ValueError(f"Unknown error type: {error_type}")

        # Let user select error type
        error_types = [
            "Configuration Error - Test config validation and handling",
            "Plugin Error - Test plugin error handling",
            "Command Error - Test command execution errors",
            "Security Error - Test security violation handling"
        ]

        try:
            # Show error handling info
            self.ui.info("\nThis demo shows how Chui handles different types of errors:")
            self.ui.info("- Structured error handling with categories")
            self.ui.info("- Error severity levels")
            self.ui.info("- Contextual error information")
            self.ui.info("- Error recovery mechanisms\n")

            error_choice = self.ui.select_from_list(error_types, "Select an error type to simulate:")
            error_type = error_choice.split(" - ")[0]

            self.ui.info(f"\nSimulating {error_type}...")
            try:
                trigger_error(error_type.split()[0].lower())
            except Exception as e:
                self.error_handler.handle(
                    error=e,
                    category=ErrorCategory.PLUGIN,
                    severity=ErrorSeverity.WARNING,
                    operation="error_handling_demo",
                    context={'demo_type': error_type},
                    debug=self.debug
                )

            self.ui.info("\nError was caught and handled properly!")
            return True

        except Exception as e:
            self.ui.error(f"Error in error handling demo: {str(e)}")
            if self.debug:
                import traceback
                self.ui.debug("Traceback:\n" + traceback.format_exc())
            return False

    def _demo_all(self) -> bool:
        """Runs all demos in sequence to showcase full framework capabilities"""
        demos = [
            ("UI Components", self._demo_ui),
            ("Configuration", self._demo_config),
            ("Event System", self._demo_events),
            ("Command Pipeline", self._demo_pipeline),
            ("Error Handling", self._demo_error_handling)
        ]

        for name, demo in demos:
            self.ui.panel(
                "Starting " + name + " Demo",
                style="bold blue"
            )
            try:
                if not demo():
                    msg = "Demo {} had warnings/errors. Continue with next demo?"
                    if not self.ui.confirm(msg.format(name)):
                        return False
            except Exception as e:
                self.ui.error("Error in {} demo: {}".format(name, str(e)))
                if not self.ui.confirm("Continue with next demo?"):
                    return False

            self.ui.success("Completed: " + name)

        return True

    @property
    def help(self) -> str:
        return (
            "\n"
            "        Chui Framework Playground\n"
            "\n"
            "        Usage: playground [demo_name] [--help]\n"
            "\n"
            "        Available demos:\n"
            "          ui          - UI components and interactions\n"
            "          config     - Configuration management features\n"
            "          events     - Event system capabilities\n"
            "          pipeline   - Command pipeline features\n"
            "          error      - Error handling mechanisms\n"
            "          all        - Run all demonstrations\n"
            "\n"
            "        Run without arguments for interactive mode.\n"
            "        "
        )


class PlaygroundPlugin(Plugin):
    def __init__(self, ui: UI, config: Config, events: EventManager):
        super().__init__(ui, config, events)
        self._commands = {
            "playground": PlaygroundCommand(ui, config)
        }
    @property
    def name(self) -> str:
        return "playground"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "A comprehensive example plugin demonstrating all Chui framework features"

    @property
    def dependencies(self) -> List[str]:
        return []

    def _initialize(self) -> None:
        """Initialize the playground plugin"""
        try:
            if self.debug:
                self.ui.debug(f"Initializing {self.name} plugin")

            # Set initial configuration if needed
            if not self.config.get(f"{self.name}.initialized"):
                if self.debug:
                    self.ui.debug("First time initialization - setting defaults")

                self.config.set(f"{self.name}.initialized", True)
                self.config.set(f"{self.name}.last_run", "Never")
                self.config.set(f"{self.name}.run_count", 0)

                if self.debug:
                    self.ui.debug("Default configuration set")

            # Register event handlers
            self.events.subscribe(f"{self.name}.test", self._handle_test_event)

            if self.debug:
                self.ui.debug(f"{self.name} plugin initialization complete")

        except Exception as e:
            raise PluginError(f"Failed to initialize {self.name} plugin: {str(e)}")

    def _cleanup(self) -> None:
        """Cleanup playground resources"""
        try:
            if self.debug:
                self.ui.debug(f"Cleaning up {self.name} plugin")

            # Update last run time before cleanup
            self.config.set(f"{self.name}.last_run", datetime.now().isoformat())

            if self.debug:
                self.ui.debug(f"{self.name} plugin cleanup complete")

        except Exception as e:
            self.ui.error(f"Error during {self.name} plugin cleanup: {str(e)}")

    def _handle_test_event(self, event: Event) -> None:
        """Handle playground test events"""
        if self.debug:
            self.ui.debug(f"Handling test event: {event.name}")
            self.ui.debug(f"Event data: {event.data}")

    def get_commands(self) -> Dict[str, Type[BaseCommand]]:
        """Get plugin commands"""
        return {
            "playground": PlaygroundCommand
        }

    def get_hooks(self) -> Dict[str, Any]:
        """Get plugin event hooks"""
        return {
            f"{self.name}.test": self._handle_test_event
        }


def setup(cli: CLIProtocol) -> None:
    """Register the playground command with the CLI"""
    try:
        # Create plugin instance first
        plugin = PlaygroundPlugin(cli.ui, cli.config, cli.events)

        # Initialize plugin
        plugin.initialize()

        # Register commands
        for cmd_name, cmd_class in plugin.get_commands().items():
            cli.register_plugin_command(cmd_name, cmd_class)

        if hasattr(cli, 'ui'):
            cli.ui.debug("Playground plugin commands registered successfully")

    except Exception as e:
        if hasattr(cli, 'ui'):
            cli.ui.error(f"Failed to register playground commands: {str(e)}")
        raise

