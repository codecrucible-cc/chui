"""
Core UI functionality for CHUI framework.
"""

import os
import sys
from typing import Optional, Any, List, Dict, Union, Callable, Literal

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
import cmd2

from .capabilities import UICapabilities
from .formatters import TextFormatter


class BaseUI:
    """Base UI class with core functionality"""

    def __init__(self, console: Optional[Console] = None, cmd: Optional[cmd2.Cmd] = None):
        self.capabilities = UICapabilities()

        # Initialize console with explicit color system
        if console is None:
            color_system = self._detect_color_system()
            self.console = Console(
                force_terminal=self.capabilities.is_interactive,
                color_system=color_system
            )
        else:
            self.console = console

        self.cmd = cmd
        self.formatter = TextFormatter()

    def _detect_color_system(self) -> Optional[Literal['auto', 'standard', 'windows', 'truecolor', '256', None]]:
        """Detect appropriate color system based on terminal capabilities"""
        if not self.capabilities.has_color:
            return None

        if self.capabilities.system == 'windows':
            # Windows 10+ can usually handle truecolor
            if 'WT_SESSION' in os.environ:  # Windows Terminal
                return 'truecolor'
            if 'TERM_PROGRAM' in os.environ:  # VS Code, etc.
                return 'truecolor'
            if os.environ.get('TERM') == 'xterm-256color':
                return '256'
            return 'windows'  # Fallback to basic Windows colors

        # Unix-like systems
        if os.environ.get('COLORTERM') in ('truecolor', '24bit'):
            return 'truecolor'
        if os.environ.get('TERM', '').endswith('-256color'):
            return '256'
        return 'standard'

    def safe_print(self, content: str, style: Optional[str] = None) -> None:
        """Print with fallbacks for different terminal capabilities"""
        try:
            if style and self.capabilities.has_color:
                self.console.print(content, style=style)
            else:
                # Strip any remaining style markers for non-color output
                content = self.formatter.strip_style_markers(content)
                print(content)
        except Exception as e:
            # Ultimate fallback
            content = self.formatter.strip_style_markers(content)
            print(content)
    
    def prompt(self, 
               message: str, 
               choices: Optional[List[str]] = None, 
               default: Optional[str] = None) -> str:
        """Request user input with optional choices"""
        # Use cmd2's built-in input if available, otherwise fall back to rich
        if self.cmd:
            return self.cmd.read_input(message + ' ')
        return Prompt.ask(message, choices=choices, default=default)
    
    def confirm(self, 
                message: str, 
                default: bool = False) -> bool:
        """Ask for user confirmation"""
        if self.cmd:
            response = self.cmd.read_input(f"{message} [y/n] ").lower()
            return response.startswith('y')
        return Confirm.ask(message, default=default)
    
    def select_from_list(self, 
                        items: List[Any], 
                        message: str = "Select an option:",
                        show_indices: bool = True) -> Any:
        """Present a list of items for user selection"""
        for idx, item in enumerate(items, 1):
            self.console.print(f"{idx if show_indices else ''} {item}")
        
        while True:
            if self.cmd:
                choice = self.cmd.read_input(f"{message} ")
            else:
                choice = Prompt.ask(message, choices=[str(i) for i in range(1, len(items) + 1)])
            
            try:
                return items[int(choice) - 1]
            except (ValueError, IndexError):
                self.error("Invalid selection, please try again")
    
    def panel(self, 
             content: str, 
             title: Optional[str] = None,
             style: str = "none") -> None:
        """Display content in a panel"""
        self.console.print(Panel(content, title=title, style=style))
    
    def error(self, message: str) -> None:
        """Display error message"""
        self.safe_print(f"Error: {message}", style="red")
    
    def success(self, message: str) -> None:
        """Display success message"""
        self.safe_print(f"✓ {message}" if self.capabilities.unicode_support else "* {message}",
                       style="green")
    
    def warning(self, message: str) -> None:
        """Display warning message"""
        self.safe_print(f"! {message}", style="yellow")
    
    def info(self, message: str) -> None:
        """Display info message"""
        self.safe_print(f"ℹ {message}" if self.capabilities.unicode_support else "i {message}",
                       style="blue")
    
    def debug(self, message: str) -> None:
        """Display debug message"""
        self.safe_print(message, style="dim")

    def link(self, text: str, url: str) -> None:
        """Display a clickable link"""
        if self.capabilities.is_interactive:
            self.console.print(f"[link={url}]{text}[/link]")
        else:
            self.console.print(f"{text} ({url})")
    
    def link_list(self, links: List[Dict[str, str]], title: Optional[str] = None) -> None:
        """Display a list of clickable links with descriptions"""
        if title:
            self.console.print(f"\n[bold]{title}[/bold]")
        
        for link in links:
            desc = link.get('description', '')
            if desc:
                self.console.print(f"• {desc}")
            self.console.print(f"  [link={link['url']}]{link['url']}[/link]")
        
        self.console.print()
    
    def markdown_with_links(self, content: str) -> None:
        """Display markdown content that can contain clickable links"""
        md = Markdown(content)
        self.console.print(md)

    def get_terminal_width(self) -> int:
        """Get current terminal width"""
        return self.capabilities.get_terminal_width()

    def get_terminal_height(self) -> int:
        """Get current terminal height"""
        return self.capabilities.get_terminal_height()

    def adjust_output_for_terminal(self, content: str, max_width: Optional[int] = None) -> str:
        """Adjust content to fit terminal constraints"""
        width = max_width or self.get_terminal_width()
        if len(content) > width:
            return content[:width - 3] + "..."
        return content
    
    # Basic table implementation that will be extended in displays/tables.py
    def table(self, 
             headers: List[str], 
             rows: List[List[Any]], 
             title: Optional[str] = None) -> None:
        """Display data in a formatted table"""
        from rich.table import Table
        
        if self.capabilities.is_interactive:
            # Use rich table for interactive terminals
            table = Table(title=title)
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self.console.print(table)
        else:
            # Fallback to simple format for non-interactive terminals
            if title:
                print(f"\n{title}")
            # Print headers
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + (3 * (len(headers) - 1))))
            # Print rows
            for row in rows:
                print(" | ".join(str(cell) for cell in row))

    # Methods to integrate with the extended modules that we'll implement
    def paginated_table(self, *args, **kwargs) -> None:
        """Placeholder for paginated table - will be implemented in UI class"""
        pass
    
    def progress_bar(self, *args, **kwargs) -> None:
        """Placeholder for progress bar - will be implemented in UI class"""
        pass
    
    def input_form(self, *args, **kwargs) -> None:
        """Placeholder for input form - will be implemented in UI class"""
        pass