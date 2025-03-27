# Chui Framework
## Command-Line Hub & UI Interface Framework

Chui is a robust framework built on top of cmd2 that provides an extensible, plugin-based architecture for building sophisticated command-line applications. It combines the power of cmd2's command processing with a comprehensive set of UI components, event handling, and infrastructure management capabilities.

## Overview

Chui enhances command-line applications by providing:
- Rich UI components and consistent user interaction patterns
- Plugin-based architecture for modular functionality
- Event system for loose coupling between components
- Configuration management with secure storage
- Comprehensive error handling and debugging
- Command pipeline for complex operations
- Cross-platform terminal and file system abstraction

## Key Features

### Rich UI Components
- Consistent message types (info, success, warning, error, debug)
- Interactive prompts and confirmations
- Formatted tables with pagination, sorting, and filtering
- Styled panels with multi-section support
- Interactive forms with validation
- List selection components
- Color-coded output (with terminal capability detection)
- Unicode support (with automatic detection)
- Terminal-aware formatting

### Plugin System
- Hot-loadable plugins
- Dependency management
- Event-driven communication
- Automatic command registration
- Plugin lifecycle management (initialize/cleanup)
- Configuration persistence
- Plugin creation utilities

### Command Pipeline
- Structured command execution
- Namespaced commands support
- Pre/post execution hooks
- Error handling and recovery
- Operation context tracking
- Command result management
- Timeout handling
- Remote execution capabilities (planned)

### Configuration Management
- Hierarchical configuration storage
- Secure value encryption
- Dynamic default values
- Configuration validation
- System-aware defaults
- Configuration UI
- Automatic backup

### Event System
- Event subscription/publication
- Operation correlation
- Event timeline tracking
- Event contexts
- Custom event handlers
- Event management

### Error Handling
- Categorized errors
- Severity levels
- Error context tracking
- Recovery mechanisms
- Debug output
- Error logging
- Security-specific error handling

### Cross-Platform Utilities
- Path management (Windows, macOS, Linux)
- Terminal capabilities detection
- Process management
- Signal handling
- Locale management
- Temporary file handling
- Network utilities

## Use Cases

### Application Framework
Chui excels as a foundation for building:
- System administration tools
- Development utilities
- Monitoring applications
- Configuration managers
- Service controllers
- Deployment tools

### Infrastructure Management
Perfect for creating:
- Server management consoles
- Network configuration tools
- System monitoring interfaces
- Service deployment tools
- Resource managers
- Backup utilities

### Development Tools
Ideal for building:
- Build system interfaces
- Code generation tools
- Project scaffolding
- Testing frameworks
- Debug consoles
- Development workflows

### Interactive Applications
Well-suited for:
- Data analysis tools
- Interactive shells
- Configuration wizards
- System diagnostics
- Resource monitors
- Process managers

## Getting Started

### Installation & Running

```bash
# Clone the repository
git clone https://github.com/your-repo/chui
cd chui
```

#### Install & Run
```bash
pip install .
chui
```

#### Develop & Run
```bash
pip install -e .
chui
```

#### Run Locally
```bash
python -m chui
```

### Basic Usage

```python
# Create a simple CLI application
from chui.cli import ChuiCLI

def main():
    cli = ChuiCLI()
    cli.cmdloop()

if __name__ == "__main__":
    main()
```

### Plugin Development

You can quickly create a new plugin using the built-in utility:

```bash
python -m chui.core.create_plugin myplugin
```

Or create a plugin manually:

```python
from chui.plugins.base import Plugin
from chui.commands import BaseCommand, CommandContext

class MyCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "mycommand"
        
    def run(self, context: CommandContext) -> Any:
        self.ui.info("Executing command...")
        # Command implementation
        return True

class MyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_commands(self):
        return {"mycommand": MyCommand}
        
    def _initialize(self):
        # Plugin initialization
        pass
        
    def _cleanup(self):
        # Plugin cleanup
        pass
```

## Architecture

### Component Overview
```
chui/
├── __main__.py     # Entry point
├── cli.py          # Main CLI application
├── commands/       # Command system
├── config.py       # Configuration management
├── core/           # Core functionality
├── events/         # Event system
├── plugins/        # Plugin management
├── protocols.py    # Protocol definitions
├── ui/             # UI components
└── utilities/      # Utility modules
```

### Key Components
- **CLI**: Central command processor and plugin coordinator
- **UI**: User interaction and display management
- **Plugins**: Modular functionality extensions
- **Events**: Inter-component communication
- **Commands**: Command execution and pipeline
- **Config**: Configuration management

## Development Tools

Chui includes development tools:
- Playground plugin for feature exploration
- Debug mode for development
- Command templating
- Plugin scaffolding
- Settings management UI
- Error handling with context

## Examples

### Running Chui
```bash
python -m chui
```

### Running the Chui Playground demo
```bash
python demo.py
```

### Creating a Custom Command
```python
class MyCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "mycommand"
        
    def run(self, context: CommandContext) -> Any:
        if context.flags.get('verbose'):
            self.ui.debug("Verbose mode")
            
        self.ui.info("Processing...")
        
        if 'name' in context.options:
            self.ui.success(f"Hello, {context.options['name']}!")
        
        return True
```

### User Interaction
```python
# Get user input
name = self.ui.prompt("Enter your name:")

# Confirm with user
if self.ui.confirm("Are you sure?", default=False):
    self.ui.success("Confirmed!")

# Show options
options = ["Option 1", "Option 2", "Option 3"]
choice = self.ui.select_option(options, title="Select an option")

# Display results
self.ui.table(
    headers=["Name", "Value"],
    rows=[["Option", choice]]
)

# Create a form
from chui.ui.components.forms import FormField, FieldType
fields = [
    FormField(
        name="username",
        label="Username",
        field_type=FieldType.STRING,
        required=True
    ),
    FormField(
        name="password",
        label="Password",
        field_type=FieldType.PASSWORD,
        required=True
    )
]
result = self.ui.input_form(fields, title="Login Form")
```

### Event Handling
```python
def on_event(event):
    self.ui.info(f"Event received: {event.name}")

self.events.subscribe("my_event", on_event)

from chui.events.base import Event
from datetime import datetime
self.events.emit(Event(
    name="my_event", 
    data={"key": "value"},
    timestamp=datetime.now()
))
```

## Project Structure
```
chui/
├── chui/           # Framework core
├── plugins/        # Plugin directory
├── pyproject.toml  # Project configuration
└── README.md       # Documentation
```

## Development Status

Chui is under active development with focus on:
- Enhanced plugin capabilities
- Extended UI components
- Additional infrastructure tools
- Improved documentation
- Testing coverage
- Performance optimization

## Requirements

- Python 3.7+
- rich>=12.0.0
- cmd2>=2.4.2
- pyyaml>=6.0
- cryptography>=38.0.0

## Support

For issues, feature requests, or development questions:
- Check the playground plugin for examples
- Enable debug mode for detailed output (`chui settings set system.debug true`)
- Use the built-in settings command to explore configuration options