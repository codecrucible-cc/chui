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
- Infrastructure management capabilities

## Key Features

### Rich UI Components
- Consistent message types (info, success, warning, error)
- Interactive prompts and confirmations
- Formatted tables and panels
- Progress indicators and status updates
- Color-coded output (with fallbacks)
- Unicode support (with automatic detection)

### Plugin System
- Hot-loadable plugins
- Dependency management
- Event-driven communication
- Automatic command registration
- Plugin lifecycle management
- Configuration persistence

### Command Pipeline
- Structured command execution
- Pre/post execution hooks
- Error handling and recovery
- Operation context tracking
- Command result management
- Timeout handling

### Configuration Management
- Hierarchical configuration storage
- Secure value encryption
- Dynamic default values
- Configuration validation
- Import/export capabilities
- Automatic backup

### Event System
- Event subscription/publication
- Operation correlation
- Event timeline tracking
- Event replay capabilities
- Custom event handlers
- Event persistence

### Error Handling
- Categorized errors
- Severity levels
- Error context tracking
- Recovery mechanisms
- Debug output
- Error logging

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

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd chui

# Install dependencies
pip install -r requirements.txt
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
```bash
python -m chui create_plugin myplugin --description "My awesome plugin" --author "John Doe"
```

```python
from chui.plugins.base import Plugin
from chui.commands import BaseCommand

class MyCommand(BaseCommand):
    def execute(self, args, flags, options):
        self.ui.info("Executing command...")
        return False  # Stay in CLI

class MyPlugin(Plugin):
    @property
    def name(self): return "my_plugin"
    
    @property
    def version(self): return "1.0.0"
    
    def get_commands(self):
        return {"mycommand": MyCommand}
```

## Architecture

### Component Overview
```
chui/
├── cli.py           # Main CLI application
├── commands/        # Command system
├── core/           # Core functionality
├── events/         # Event system
├── plugins/        # Plugin management
├── ui.py           # UI components
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
- Testing utilities
- Development console

## Examples

### Running chui
```bash
python -m chui
```

### Running the chui Playground demo
```bash
python demo.py
```

### Creating a Custom Command
```python
class MyCommand(BaseCommand):
    def execute(self, args, flags, options):
        if flags.get('verbose'):
            self.ui.debug("Verbose mode")
            
        self.ui.info("Processing...")
        
        if 'name' in options:
            self.ui.success(f"Hello, {options['name']}!")
        
        return False
```

### User Interaction
```python
# Get user input
name = self.ui.prompt("Enter your name:")

# Show options
options = ["Option 1", "Option 2", "Option 3"]
choice = self.ui.select_from_list(options)

# Display results
self.ui.table(
    headers=["Name", "Value"],
    rows=[["Option", choice]]
)
```

### Event Handling
```python
def on_event(event):
    self.ui.info(f"Event received: {event.name}")

self.events.subscribe("my_event", on_event)
self.events.emit(Event("my_event", data={"key": "value"}))
```

## Project Structure
```
chui/
├── app.py          # Application entry
├── chui/           # Framework core
├── plugins/        # Plugin directory
├── tests/          # Test suite
├── docs/           # Documentation
└── requirements.txt
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

- Python 3.8+
- cmd2
- rich
- cryptography
- PyYAML

## Support

For issues, feature requests, or development questions:
- Check the playground plugin for examples
- Enable debug mode for detailed output
- Review the command documentation
