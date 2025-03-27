
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

@dataclass
class CommandContext:
    """Unified command context for all commands"""
    name: str                    # Command name
    namespace: Optional[str]     # Command namespace (if any)
    args: List[str]             # Positional arguments
    flags: Dict[str, bool]      # Boolean flags (--flag)
    options: Dict[str, str]     # Key-value options (--key value)
    original_input: str         # Original command string
    timestamp: datetime         # When command was created
    metadata: Dict[str, Any]    # Additional context data

class BaseCommand(ABC):
    """Enhanced base command class"""
    
    def __init__(self, ui, config, pipeline=None):
        self.ui = ui
        self.config = config
        self.pipeline = pipeline
        self._subcommands = {}
        self._aliases = {}
        self._help = {}
        
    @property
    def namespace(self) -> Optional[str]:
        """Command namespace"""
        return None
        
    @property
    def name(self) -> str:
        """Command name"""
        return self.__class__.__name__.lower().replace('command', '')
        
    @property
    def aliases(self) -> List[str]:
        """Command aliases"""
        return list(self._aliases.keys())

    def create_context(self, args: List[str], flags: Dict[str, bool],
                      options: Dict[str, str], input_str: str) -> CommandContext:
        """Create command context"""
        return CommandContext(
            name=self.name,
            namespace=self.namespace,
            args=args,
            flags=flags, 
            options=options,
            original_input=input_str,
            timestamp=datetime.now(),
            metadata={}
        )

    def execute(self, args: List[str], flags: Dict[str, bool],
                options: Dict[str, str], input_str: str = "") -> Any:
        """Execute command with context"""
        # Create context
        ctx = self.create_context(args, flags, options, input_str)
        
        # Handle help flag
        if flags.get('help'):
            self.show_help()
            return True
            
        # Handle debug
        debug = self.config.get('system.debug', False)
        if debug:
            self._log_debug(ctx)
            
        try:
            # Execute command
            return self.run(ctx)
        except Exception as e:
            self.ui.error(f"Error executing {self.name}: {str(e)}")
            if debug:
                self.ui.debug(f"Exception details: {str(e)}")
            return False
            
    @abstractmethod
    def run(self, context: CommandContext) -> Any:
        """Implement actual command logic"""
        pass
        
    def register_subcommand(self, name: str, handler, help_text: str = None) -> None:
        """Register a subcommand"""
        self._subcommands[name] = handler
        if help_text:
            self._help[name] = help_text
            
    def register_alias(self, alias: str, target: str) -> None:
        """Register a command alias"""
        self._aliases[alias] = target
        
    def get_subcommand(self, name: str):
        """Get subcommand handler"""
        return self._subcommands.get(name)
        
    def show_help(self) -> None:
        """Show command help"""
        self.ui.info(self.get_help())
        
    def get_help(self) -> str:
        """Get command help text"""
        # Basic help
        help_text = [
            f"\n{self.name} - {self.__doc__ or 'No description'}",
            "\nUsage:",
            f"  {self.name} [options] [args...]"
        ]
        
        # Aliases
        if self.aliases:
            help_text.extend([
                "\nAliases:",
                "  " + ", ".join(self.aliases)
            ])
            
        # Subcommands
        if self._subcommands:
            help_text.extend([
                "\nSubcommands:"
            ])
            for name, handler in self._subcommands.items():
                help_text.append(f"  {name:<15} {self._help.get(name, '')}")
                
        # Options
        help_text.extend([
            "\nOptions:",
            "  --help      Show this help message",
            "  --debug     Enable debug output"
        ])
        
        return "\n".join(help_text)
        
    def _log_debug(self, context: CommandContext) -> None:
        """Log debug information"""
        self.ui.debug(f"Executing {self.name}")
        self.ui.debug(f"Namespace: {context.namespace}")
        self.ui.debug(f"Args: {context.args}")
        self.ui.debug(f"Flags: {context.flags}")
        self.ui.debug(f"Options: {context.options}")

class NamespacedCommand(BaseCommand):
    """Enhanced namespaced command implementation"""
    
    @property
    @abstractmethod
    def namespace(self) -> str:
        """Command namespace (e.g., 'ssh')"""
        pass
        
    @property
    def default_subcommand(self) -> str:
        """Default subcommand when none specified"""
        return 'help'
        
    def run(self, context: CommandContext) -> Any:
        """Handle namespaced command execution"""
        # Get subcommand
        subcommand = context.args[0] if context.args else self.default_subcommand
        
        # Check for subcommand
        handler = self.get_subcommand(subcommand)
        if not handler:
            self.ui.error(f"Unknown subcommand: {subcommand}")
            self.show_help()
            return False
            
        # Execute subcommand
        try:
            # Update context
            context.args = context.args[1:]
            context.metadata['subcommand'] = subcommand
            return handler(context)
        except Exception as e:
            self.ui.error(f"Error in subcommand {subcommand}: {str(e)}")
            if self.config.get('system.debug'):
                self.ui.debug(f"Exception details: {str(e)}")
            return False