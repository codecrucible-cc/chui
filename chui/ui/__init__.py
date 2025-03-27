"""
UI Package for CHUI Framework.

This package provides enhanced UI components, displays, and utilities
for building command-line interfaces in the CHUI framework.
"""

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
import os
import sys

from rich.console import Console
import cmd2

from .core import BaseUI
from .capabilities import UICapabilities
from .pagination import Paginator, Page, FilterablePaginator
from .displays.tables import TableDisplayManager, TableConfig, TableBuilder, ColumnConfig
from .displays.panels import PanelManager, PanelType, PanelSection
from .components.forms import FormManager, FormField, FormResult
from .components.selector import ListSelector, SelectionMode, SelectionResult


T = TypeVar('T')


class UI(BaseUI):
    """
    Enhanced UI class for CHUI framework with advanced display capabilities.
    
    This class integrates all UI components, displays, and utilities into a
    unified interface for use in the CHUI framework.
    """
    
    def __init__(self, console: Optional[Console] = None, cmd: Optional[cmd2.Cmd] = None):
        """
        Initialize the enhanced UI
        
        Args:
            console: Optional Rich console instance
            cmd: Optional cmd2 instance for terminal integration
        """
        super().__init__(console, cmd)
        
        # Initialize component managers
        self.table_manager = TableDisplayManager(self.console)
        self.panel_manager = PanelManager(self.console)
        self.form_manager = FormManager(self.console)
        
    # Enhanced table methods
    def paginated_table(self,
                       headers: List[str],
                       rows: List[List[Any]],
                       title: Optional[str] = None,
                       page: int = 1,
                       page_size: int = 10,
                       show_pagination: bool = True) -> None:
        """
        Display a paginated table
        
        Args:
            headers: Column headers
            rows: Table row data
            title: Optional table title
            page: Current page number (1-based)
            page_size: Number of rows per page
            show_pagination: Whether to show pagination controls
        """
        # Convert rows to dict format for TableDisplayManager
        dict_rows = []
        for row in rows:
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header.lower().replace(' ', '_')] = row[i]
                else:
                    row_dict[header.lower().replace(' ', '_')] = None
            dict_rows.append(row_dict)
            
        # Create table config
        config = TableConfig(title=title)
        for header in headers:
            config.add_column(ColumnConfig(
                name=header.lower().replace(' ', '_'),
                header=header
            ))
            
        # Display the paginated table
        self.table_manager.display_paginated_table(
            dict_rows,
            config,
            page=page,
            page_size=page_size,
            show_pagination=show_pagination
        )
        
    def advanced_table(self,
                      data: List[Dict[str, Any]],
                      columns: List[Union[str, Dict[str, Any]]],
                      title: Optional[str] = None,
                      style: Optional[str] = None) -> None:
        """
        Display an advanced table with more customization
        
        Args:
            data: List of dictionaries representing rows
            columns: List of column names or column configuration dictionaries
            title: Optional table title
            style: Optional style for the table
        """
        # Create table config
        config = TableConfig(title=title)
        
        # Add columns
        for i, column in enumerate(columns):
            if isinstance(column, str):
                config.add_column(ColumnConfig(
                    name=column,
                    header=column.replace('_', ' ').title(),
                    display_index=i
                ))
            else:
                config.add_column(ColumnConfig(
                    name=column['name'],
                    header=column.get('header', column['name'].replace('_', ' ').title()),
                    width=column.get('width'),
                    align=column.get('align'),
                    style=column.get('style'),
                    format_func=column.get('format_func'),
                    display_index=i
                ))
                
        # Display table
        self.table_manager.display_table(data, config)
        
    def interactive_table(self,
                         data: List[Dict[str, Any]],
                         columns: List[Union[str, Dict[str, Any]]],
                         title: Optional[str] = None,
                         page_size: int = 10) -> None:
        """
        Display an interactive table with navigation
        
        Args:
            data: List of dictionaries representing rows
            columns: List of column names or column configuration dictionaries
            title: Optional table title
            page_size: Number of rows per page
        """
        # Create table config
        config = TableConfig(title=title)
        
        # Add columns
        for i, column in enumerate(columns):
            if isinstance(column, str):
                config.add_column(ColumnConfig(
                    name=column,
                    header=column.replace('_', ' ').title(),
                    display_index=i
                ))
            else:
                config.add_column(ColumnConfig(
                    name=column['name'],
                    header=column.get('header', column['name'].replace('_', ' ').title()),
                    width=column.get('width'),
                    align=column.get('align'),
                    style=column.get('style'),
                    format_func=column.get('format_func'),
                    display_index=i
                ))
                
        # Display interactive table
        self.table_manager.interactive_table(data, config, page_size=page_size)
        
    # Enhanced panel methods
    def info_panel(self,
                  content: str,
                  title: Optional[str] = None) -> None:
        """Display an information panel"""
        self.panel_manager.display_info_panel(content, title)
        
    def success_panel(self,
                     content: str,
                     title: Optional[str] = None) -> None:
        """Display a success panel"""
        self.panel_manager.display_success_panel(content, title)
        
    def warning_panel(self,
                     content: str,
                     title: Optional[str] = None) -> None:
        """Display a warning panel"""
        self.panel_manager.display_warning_panel(content, title)
        
    def error_panel(self,
                   content: str,
                   title: Optional[str] = None) -> None:
        """Display an error panel"""
        self.panel_manager.display_error_panel(content, title)
        
    def help_panel(self,
                  content: str,
                  title: Optional[str] = None) -> None:
        """Display a help panel with markdown formatting"""
        self.panel_manager.display_help_panel(content, title)
        
    def dict_panel(self,
                  data: Dict[str, Any],
                  title: Optional[str] = None) -> None:
        """Display a dictionary as a formatted panel"""
        self.panel_manager.display_dict_panel(data, title)
        
    # Form methods
    def input_form(self,
                  fields: List[FormField],
                  title: Optional[str] = None) -> FormResult:
        """
        Display an interactive form and collect user input
        
        Args:
            fields: List of form fields
            title: Optional form title
            
        Returns:
            FormResult with user input values and validation results
        """
        return self.form_manager.display_form(fields, title)
        
    # Selection methods
    def select_option(self,
                     options: List[str],
                     title: Optional[str] = None,
                     instruction: Optional[str] = None) -> Optional[str]:
        """
        Display a simple option selector and return selected option
        
        Args:
            options: List of option strings
            title: Optional title
            instruction: Optional instruction text
            
        Returns:
            Selected option or None if cancelled
        """
        selector = ListSelector(
            console=self.console,
            items=options,
            mode=SelectionMode.SINGLE,
            title=title,
            instruction=instruction
        )
        
        result = selector.display()
        return result.selected[0] if not result.cancelled and result.selected else None
        
    def select_multiple(self,
                       options: List[str],
                       title: Optional[str] = None,
                       instruction: Optional[str] = None,
                       pre_selected: Optional[List[int]] = None) -> List[str]:
        """
        Display a multiple selection list and return selected options
        
        Args:
            options: List of option strings
            title: Optional title
            instruction: Optional instruction text
            pre_selected: Optional list of pre-selected indices (0-based)
            
        Returns:
            List of selected options (empty if cancelled)
        """
        from .components.selector import select_multiple
        return select_multiple(
            console=self.console,
            options=options,
            title=title,
            instruction=instruction,
            pre_selected=pre_selected
        )


# Import package contents for easier access
__all__ = [
    'UI',
    'UICapabilities',
    'Paginator',
    'Page',
    'FilterablePaginator',
    'TableConfig',
    'ColumnConfig',
    'TableBuilder',
    'PanelType',
    'PanelSection',
    'FormField',
    'FormResult',
    'SelectionMode',
    'SelectionResult'
]