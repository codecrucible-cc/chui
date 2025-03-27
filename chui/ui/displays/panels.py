"""
Enhanced panel display functionality for CHUI UI system.

This module provides richer panel displays including:
- Information panels with sections
- Status panels
- Warning and error panels
- Help panels with formatting
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.padding import Padding
from rich.columns import Columns
from rich.text import Text
from rich.markdown import Markdown


class PanelType(Enum):
    """Types of panels with predefined styles"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    HELP = "help"
    DEBUG = "debug"
    DEFAULT = "default"


@dataclass
class PanelStyleConfig:
    """Configuration for panel styling"""
    title_style: str = "bold"
    border_style: str = "dim"
    padding: Union[int, List[int]] = 1
    expand: bool = True
    

@dataclass
class PanelSection:
    """Section within a multi-section panel"""
    title: Optional[str] = None
    content: str = ""
    style: Optional[str] = None


class PanelManager:
    """Manages enhanced panel displays"""
    
    # Default styles for different panel types
    DEFAULT_STYLES = {
        PanelType.INFO: PanelStyleConfig(
            title_style="bold blue",
            border_style="blue"
        ),
        PanelType.SUCCESS: PanelStyleConfig(
            title_style="bold green",
            border_style="green"
        ),
        PanelType.WARNING: PanelStyleConfig(
            title_style="bold yellow",
            border_style="yellow"
        ),
        PanelType.ERROR: PanelStyleConfig(
            title_style="bold red",
            border_style="red"
        ),
        PanelType.HELP: PanelStyleConfig(
            title_style="bold cyan",
            border_style="cyan",
            padding=2
        ),
        PanelType.DEBUG: PanelStyleConfig(
            title_style="bold magenta",
            border_style="magenta",
        ),
        PanelType.DEFAULT: PanelStyleConfig()
    }
    
    def __init__(self, console: Console):
        self.console = console
        
    def display_panel(self,
                      content: str,
                      title: Optional[str] = None,
                      panel_type: PanelType = PanelType.DEFAULT,
                      style_config: Optional[PanelStyleConfig] = None) -> None:
        """
        Display a styled panel
        
        Args:
            content: Panel content
            title: Optional panel title
            panel_type: Type of panel (determines default styling)
            style_config: Optional custom style configuration
        """
        # Get style configuration
        if style_config is None:
            style_config = self.DEFAULT_STYLES[panel_type]
            
        # Create panel
        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style=style_config.border_style,
            padding=style_config.padding,
            expand=style_config.expand
        )
        
        # Display panel
        self.console.print(panel)
        
    def display_info_panel(self,
                          content: str,
                          title: Optional[str] = None) -> None:
        """Display an information panel"""
        self.display_panel(content, title, PanelType.INFO)
        
    def display_success_panel(self,
                             content: str,
                             title: Optional[str] = None) -> None:
        """Display a success panel"""
        self.display_panel(content, title, PanelType.SUCCESS)
        
    def display_warning_panel(self,
                             content: str,
                             title: Optional[str] = None) -> None:
        """Display a warning panel"""
        self.display_panel(content, title, PanelType.WARNING)
        
    def display_error_panel(self,
                           content: str,
                           title: Optional[str] = None) -> None:
        """Display an error panel"""
        self.display_panel(content, title, PanelType.ERROR)
        
    def display_help_panel(self,
                          content: str,
                          title: Optional[str] = None) -> None:
        """Display a help panel with markdown formatting"""
        # Format content as markdown
        md = Markdown(content)
        self.display_panel(md, title, PanelType.HELP)
        
    def display_dict_panel(self,
                          data: Dict[str, Any],
                          title: Optional[str] = None,
                          panel_type: PanelType = PanelType.INFO) -> None:
        """
        Display a dictionary as a formatted panel
        
        Args:
            data: Dictionary to display
            title: Optional panel title
            panel_type: Type of panel
        """
        # Format dictionary
        content = []
        
        for key, value in data.items():
            # Format key
            formatted_key = key.replace('_', ' ').title()
            
            # Format value based on type
            if isinstance(value, dict):
                formatted_value = "\n  " + "\n  ".join(
                    f"{k}: {v}" for k, v in value.items()
                )
            elif isinstance(value, list):
                if value:
                    formatted_value = "\n  - " + "\n  - ".join(str(v) for v in value)
                else:
                    formatted_value = "[]"
            else:
                formatted_value = str(value)
                
            content.append(f"[bold]{formatted_key}:[/bold] {formatted_value}")
            
        # Create and display panel
        self.display_panel("\n".join(content), title, panel_type)
        
    def display_multi_section_panel(self,
                                   sections: List[PanelSection],
                                   title: Optional[str] = None,
                                   panel_type: PanelType = PanelType.DEFAULT) -> None:
        """
        Display a panel with multiple sections
        
        Args:
            sections: List of panel sections
            title: Overall panel title
            panel_type: Type of panel
        """
        # Format sections
        content = []
        
        for i, section in enumerate(sections):
            # Add section title if provided
            if section.title:
                section_style = section.style or "bold"
                content.append(f"[{section_style}]{section.title}[/{section_style}]")
                
            # Add section content
            content.append(section.content)
            
            # Add separator between sections (except the last one)
            if i < len(sections) - 1:
                content.append("\n" + "─" * 40 + "\n")
                
        # Create and display panel
        self.display_panel("\n".join(content), title, panel_type)
        
    def display_side_by_side_panels(self,
                                   left_content: str,
                                   right_content: str,
                                   left_title: Optional[str] = None,
                                   right_title: Optional[str] = None,
                                   panel_type: PanelType = PanelType.DEFAULT) -> None:
        """
        Display two panels side by side
        
        Args:
            left_content: Content for left panel
            right_content: Content for right panel
            left_title: Optional title for left panel
            right_title: Optional title for right panel
            panel_type: Type of panels
        """
        # Get style configuration
        style_config = self.DEFAULT_STYLES[panel_type]
        
        # Create panels
        left_panel = Panel(
            left_content,
            title=left_title,
            title_align="left",
            border_style=style_config.border_style,
            padding=style_config.padding
        )
        
        right_panel = Panel(
            right_content,
            title=right_title,
            title_align="left",
            border_style=style_config.border_style,
            padding=style_config.padding
        )
        
        # Create columns layout
        columns = Columns([left_panel, right_panel])
        
        # Display columns
        self.console.print(columns)


def create_section(title: Optional[str] = None, 
                  content: str = "", 
                  style: Optional[str] = None) -> PanelSection:
    """
    Create a panel section
    
    Args:
        title: Optional section title
        content: Section content
        style: Optional style for section title
        
    Returns:
        PanelSection object
    """
    return PanelSection(title=title, content=content, style=style)