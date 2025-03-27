"""
Advanced table display functionality for CHUI UI system.

This module provides enhanced table display capabilities including:
- Column formatting
- Column alignment
- Highlighting and styling
- Sorting
- Filtering
- Pagination integration
"""

from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from rich.console import Console
from rich.table import Table as RichTable
from rich.style import Style
from rich.text import Text

from ..pagination import Paginator, Page


class ColumnAlign(Enum):
    """Column alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    DECIMAL = "decimal"


@dataclass
class ColumnConfig:
    """Configuration for a table column"""
    name: str
    header: str = ""  # Display name (defaults to name if empty)
    width: Optional[int] = None
    align: ColumnAlign = ColumnAlign.LEFT
    style: Optional[str] = None
    format_func: Optional[Callable[[Any], str]] = None
    sortable: bool = True
    filterable: bool = True
    max_width: Optional[int] = None
    display_index: int = 0  # For ordering columns
    visible: bool = True
    
    def __post_init__(self):
        if not self.header:
            self.header = self.name.replace('_', ' ').title()


@dataclass
class TableConfig:
    """Configuration for an enhanced table"""
    columns: List[ColumnConfig] = field(default_factory=list)
    title: Optional[str] = None
    show_header: bool = True
    show_footer: bool = False
    show_lines: bool = True
    border_style: str = "dim"
    header_style: str = "bold"
    row_styles: List[str] = field(default_factory=lambda: ["", "dim"])
    highlight_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    highlight_style: str = "yellow"
    no_data_message: str = "No data available"
    
    def add_column(self, column: Union[str, ColumnConfig]) -> 'TableConfig':
        """Add a column to the table configuration"""
        if isinstance(column, str):
            column = ColumnConfig(name=column)
        self.columns.append(column)
        return self
    
    def get_visible_columns(self) -> List[ColumnConfig]:
        """Get only visible columns sorted by display_index"""
        return sorted(
            [col for col in self.columns if col.visible], 
            key=lambda c: c.display_index
        )


class TableDisplayManager:
    """Manages table display rendering and interaction"""
    
    def __init__(self, console: Console):
        self.console = console
        
    def display_table(self, 
                     data: List[Dict[str, Any]], 
                     config: TableConfig) -> None:
        """
        Display a table with the given data and configuration
        
        Args:
            data: List of data rows (as dictionaries)
            config: Table configuration
        """
        if not data:
            self.console.print(config.no_data_message, style="dim")
            return
            
        # Create Rich table
        table = RichTable(
            title=config.title,
            show_header=config.show_header,
            show_footer=config.show_footer,
            show_lines=config.show_lines,
            border_style=config.border_style
        )
        
        # Add columns
        visible_columns = config.get_visible_columns()
        for column in visible_columns:
            table.add_column(
                column.header,
                justify=column.align.value,
                style=column.style,
                width=column.width,
                max_width=column.max_width,
                header_style=config.header_style
            )
            
        # Add rows
        for i, row_data in enumerate(data):
            # Apply alternating row styles
            row_style = config.row_styles[i % len(config.row_styles)] if config.row_styles else None
            
            # Apply highlight if applicable
            if config.highlight_func and config.highlight_func(row_data):
                row_style = config.highlight_style
                
            # Format row cells
            cells = []
            for column in visible_columns:
                value = row_data.get(column.name, "")
                
                # Apply formatting if specified
                if column.format_func and value is not None:
                    try:
                        formatted_value = column.format_func(value)
                    except Exception:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value) if value is not None else ""
                
                # Apply styling
                if column.style:
                    cell = Text(formatted_value, style=column.style)
                else:
                    cell = formatted_value
                    
                cells.append(cell)
                
            table.add_row(*cells, style=row_style)
            
        # Display the table
        self.console.print(table)
        
    def display_paginated_table(self,
                               data: List[Dict[str, Any]],
                               config: TableConfig,
                               page: int = 1,
                               page_size: int = 10,
                               show_pagination: bool = True) -> None:
        """
        Display a paginated table
        
        Args:
            data: List of data rows (as dictionaries)
            config: Table configuration
            page: Current page number (1-based)
            page_size: Number of items per page
            show_pagination: Whether to show pagination controls
        """
        # Handle empty data case
        if not data:
            self.console.print(config.no_data_message, style="dim")
            return
            
        # Paginate the data
        paginator = Paginator(data, page_size)
        page_obj = paginator.get_page(page)
        
        # Display the current page
        self.display_table(page_obj.items, config)
        
        # Show pagination information if requested
        if show_pagination:
            self._display_pagination_info(page_obj)
            
    def _display_pagination_info(self, page: Page) -> None:
        """Display pagination information and controls"""
        # Create pagination text
        text = Text()
        text.append(f"\nPage {page.page_number} of {page.total_pages} ", style="bold")
        text.append(f"(showing {len(page.items)} of {page.total_items} items)", style="dim")
        
        # Add page navigation hints
        if page.has_previous or page.has_next:
            text.append("\nNavigate: ", style="italic")
            
            if page.has_previous:
                text.append("p", style="bold cyan")
                text.append("revious | ")
                
            if page.has_next:
                text.append("n", style="bold cyan")
                text.append("ext")
                
        self.console.print(text)
        
    def interactive_table(self,
                         data: List[Dict[str, Any]],
                         config: TableConfig,
                         page_size: int = 10,
                         filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
                         sort_key: Optional[str] = None,
                         reverse: bool = False) -> None:
        """
        Display an interactive table with pagination, sorting, and filtering
        
        Args:
            data: List of data rows (as dictionaries)
            config: Table configuration
            page_size: Number of items per page
            filter_func: Optional function to filter data rows
            sort_key: Optional key to sort by
            reverse: Whether to reverse the sort order
        """
        # Apply filtering if provided
        if filter_func:
            filtered_data = [row for row in data if filter_func(row)]
        else:
            filtered_data = data
            
        # Apply sorting if provided
        if sort_key:
            column = next((c for c in config.columns if c.name == sort_key), None)
            if column and column.sortable:
                try:
                    filtered_data = sorted(
                        filtered_data, 
                        key=lambda x: x.get(sort_key, ""), 
                        reverse=reverse
                    )
                except Exception:
                    # Fall back to string comparison if sorting fails
                    filtered_data = sorted(
                        filtered_data, 
                        key=lambda x: str(x.get(sort_key, "")), 
                        reverse=reverse
                    )
        
        # Create paginator with the filtered and sorted data
        paginator = Paginator(filtered_data, page_size)
        current_page = 1
        
        # Display initial page
        while True:
            # Clear previous output (if supported)
            self.console.clear()
            
            # Show the current page
            page_obj = paginator.get_page(current_page)
            self.display_table(page_obj.items, config)
            self._display_pagination_info(page_obj)
            
            # Get user input for navigation
            choice = input("\nEnter command (q to quit): ").lower().strip()
            
            if choice == 'q':
                break
            elif choice == 'n' and page_obj.has_next:
                current_page += 1
            elif choice == 'p' and page_obj.has_previous:
                current_page -= 1
            elif choice.isdigit():
                page_num = int(choice)
                if 1 <= page_num <= page_obj.total_pages:
                    current_page = page_num


class TableBuilder:
    """Builder pattern for creating and configuring tables"""
    
    def __init__(self, title: Optional[str] = None):
        self.config = TableConfig(title=title)
        self.data: List[Dict[str, Any]] = []
        
    def add_column(self, 
                  name: str, 
                  header: Optional[str] = None, 
                  **kwargs) -> 'TableBuilder':
        """Add a column to the table"""
        col_config = ColumnConfig(
            name=name,
            header=header or name.replace('_', ' ').title(),
            **kwargs
        )
        self.config.add_column(col_config)
        return self
        
    def add_data(self, data: List[Dict[str, Any]]) -> 'TableBuilder':
        """Set the table data"""
        self.data = data
        return self
        
    def set_title(self, title: str) -> 'TableBuilder':
        """Set the table title"""
        self.config.title = title
        return self
        
    def set_row_styles(self, styles: List[str]) -> 'TableBuilder':
        """Set alternating row styles"""
        self.config.row_styles = styles
        return self
        
    def set_highlight_func(self, 
                          func: Callable[[Dict[str, Any]], bool], 
                          style: str = "yellow") -> 'TableBuilder':
        """Set row highlighting function and style"""
        self.config.highlight_func = func
        self.config.highlight_style = style
        return self
        
    def build(self) -> Tuple[List[Dict[str, Any]], TableConfig]:
        """Build the table configuration and return with data"""
        return self.data, self.config


# Factory function for creating table builders
def create_table(title: Optional[str] = None) -> TableBuilder:
    """Create a new table builder"""
    return TableBuilder(title)