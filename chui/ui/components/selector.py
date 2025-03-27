"""
Selection components for CHUI UI system.

This module provides interactive selection components for choosing from lists.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt


T = TypeVar('T')


class SelectionMode(Enum):
    """Selection modes for list selectors"""
    SINGLE = "single"      # Select a single item
    MULTIPLE = "multiple"  # Select multiple items
    PAGINATED = "paginated"  # Paginated selection


@dataclass
class SelectionItem(Generic[T]):
    """Item in a selection list"""
    value: T  # The actual value
    label: str  # Display label
    description: Optional[str] = None  # Optional description
    disabled: bool = False  # Whether the item can be selected
    selected: bool = False  # Whether the item is selected
    
    def __str__(self) -> str:
        """String representation for display"""
        return self.label


@dataclass
class SelectionResult(Generic[T]):
    """Result of a selection operation"""
    selected: List[T]  # Selected values
    indices: List[int]  # Indices of selected items
    cancelled: bool = False  # Whether selection was cancelled


class ListSelector(Generic[T]):
    """Component for selecting items from a list"""
    
    def __init__(self, 
                console: Console,
                items: List[Union[T, SelectionItem[T]]],
                mode: SelectionMode = SelectionMode.SINGLE,
                title: Optional[str] = None,
                instruction: Optional[str] = None,
                convert_func: Optional[Callable[[T], str]] = None):
        """
        Initialize a list selector
        
        Args:
            console: Rich console for display
            items: List of items or SelectionItems
            mode: Selection mode
            title: Optional title for the selection
            instruction: Optional instruction text
            convert_func: Optional function to convert raw values to display strings
        """
        self.console = console
        self.mode = mode
        self.title = title
        self.instruction = instruction or "Select an option:"
        self.convert_func = convert_func or str
        
        # Convert raw items to SelectionItems if needed
        self.items: List[SelectionItem[T]] = []
        for i, item in enumerate(items):
            if isinstance(item, SelectionItem):
                self.items.append(item)
            else:
                self.items.append(SelectionItem(
                    value=item,
                    label=self.convert_func(item)
                ))
                
    def display(self) -> SelectionResult[T]:
        """
        Display the selection list and get user selection
        
        Returns:
            SelectionResult with selected items
        """
        if self.mode == SelectionMode.SINGLE:
            return self._display_single()
        elif self.mode == SelectionMode.MULTIPLE:
            return self._display_multiple()
        else:  # PAGINATED mode
            return self._display_paginated()
            
    def _display_single(self) -> SelectionResult[T]:
        """Display single-selection list"""
        if self.title:
            self.console.print(f"[bold]{self.title}[/bold]\n")
            
        # Create table for display
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Index", style="cyan")
        table.add_column("Option")
        
        # Add items to table
        for i, item in enumerate(self.items, 1):
            label = item.label
            if item.description:
                label += f"\n[dim]{item.description}[/dim]"
                
            if item.disabled:
                label = f"[dim]{label} (disabled)[/dim]"
                
            table.add_row(str(i), label)
            
        # Display table
        self.console.print(table)
        
        # Get user selection
        while True:
            choice = Prompt.ask(self.instruction, default="1")
            
            # Check for cancel
            if choice.lower() in ('q', 'quit', 'exit', 'cancel'):
                return SelectionResult(selected=[], indices=[], cancelled=True)
                
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.items):
                    item = self.items[idx]
                    if item.disabled:
                        self.console.print("[red]This option is disabled[/red]")
                        continue
                        
                    return SelectionResult(
                        selected=[item.value],
                        indices=[idx],
                        cancelled=False
                    )
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number[/red]")
                
    def _display_multiple(self) -> SelectionResult[T]:
        """Display multiple-selection list"""
        if self.title:
            self.console.print(f"[bold]{self.title}[/bold]\n")
            
        # Create table for display
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Index", style="cyan")
        table.add_column("Selected", style="green")
        table.add_column("Option")
        
        # Add items to table
        for i, item in enumerate(self.items, 1):
            selected = "[green]✓[/green]" if item.selected else " "
            
            label = item.label
            if item.description:
                label += f"\n[dim]{item.description}[/dim]"
                
            if item.disabled:
                label = f"[dim]{label} (disabled)[/dim]"
                
            table.add_row(str(i), selected, label)
            
        # Display table
        self.console.print(table)
        
        # Show instructions
        self.console.print("\n[dim]Toggle selections by entering numbers. "
                           "Submit with 'done'. Cancel with 'q'.[/dim]")
        
        # Get user selections
        while True:
            choice = Prompt.ask(self.instruction, default="done")
            
            # Check for done/cancel
            if choice.lower() in ('done', 'ok', 'finish'):
                selected = []
                indices = []
                for i, item in enumerate(self.items):
                    if item.selected:
                        selected.append(item.value)
                        indices.append(i)
                        
                return SelectionResult(
                    selected=selected,
                    indices=indices,
                    cancelled=False
                )
            elif choice.lower() in ('q', 'quit', 'exit', 'cancel'):
                return SelectionResult(selected=[], indices=[], cancelled=True)
                
            # Toggle selection
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.items):
                    item = self.items[idx]
                    if item.disabled:
                        self.console.print("[red]This option is disabled[/red]")
                        continue
                        
                    # Toggle selection
                    item.selected = not item.selected
                    
                    # Redisplay table
                    self.console.clear()
                    if self.title:
                        self.console.print(f"[bold]{self.title}[/bold]\n")
                        
                    # Recreate table
                    table = Table(show_header=False, box=None, padding=(0, 1))
                    table.add_column("Index", style="cyan")
                    table.add_column("Selected", style="green")
                    table.add_column("Option")
                    
                    for i, item in enumerate(self.items, 1):
                        selected = "[green]✓[/green]" if item.selected else " "
                        label = item.label
                        if item.description:
                            label += f"\n[dim]{item.description}[/dim]"
                        if item.disabled:
                            label = f"[dim]{label} (disabled)[/dim]"
                        table.add_row(str(i), selected, label)
                        
                    self.console.print(table)
                    self.console.print("\n[dim]Toggle selections by entering numbers. "
                                       "Submit with 'done'. Cancel with 'q'.[/dim]")
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                if choice.lower() != "":
                    self.console.print("[red]Please enter a number, 'done', or 'q'[/red]")
                    
    def _display_paginated(self) -> SelectionResult[T]:
        """Display paginated selection list"""
        # Similar to _display_single but with pagination
        page_size = 5
        current_page = 0
        total_pages = (len(self.items) + page_size - 1) // page_size
        
        while True:
            self.console.clear()
            
            if self.title:
                self.console.print(f"[bold]{self.title}[/bold] (Page {current_page + 1}/{total_pages})\n")
                
            # Create table for current page
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Index", style="cyan")
            table.add_column("Option")
            
            # Calculate page range
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(self.items))
            
            # Add items to table
            for i in range(start_idx, end_idx):
                item = self.items[i]
                idx = i + 1  # 1-based index for display
                
                label = item.label
                if item.description:
                    label += f"\n[dim]{item.description}[/dim]"
                    
                if item.disabled:
                    label = f"[dim]{label} (disabled)[/dim]"
                    
                table.add_row(str(idx), label)
                
            # Display table
            self.console.print(table)
            
            # Show pagination controls
            self.console.print("\n[dim]Navigation: 'p' previous, 'n' next, "
                               "or enter item number to select. 'q' to cancel.[/dim]")
            
            # Get user input
            choice = Prompt.ask(self.instruction)
            
            # Handle navigation
            if choice.lower() == 'n' and current_page < total_pages - 1:
                current_page += 1
                continue
            elif choice.lower() == 'p' and current_page > 0:
                current_page -= 1
                continue
            elif choice.lower() in ('q', 'quit', 'exit', 'cancel'):
                return SelectionResult(selected=[], indices=[], cancelled=True)
                
            # Handle selection
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.items):
                    item = self.items[idx]
                    if item.disabled:
                        self.console.print("[red]This option is disabled[/red]")
                        continue
                        
                    return SelectionResult(
                        selected=[item.value],
                        indices=[idx],
                        cancelled=False
                    )
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                if choice.lower() not in ('n', 'p', ''):
                    self.console.print("[red]Please enter a number, 'n', 'p', or 'q'[/red]")


# Utility functions to create selectors
def select_option(console: Console,
                 options: List[str],
                 title: Optional[str] = None,
                 instruction: Optional[str] = None) -> Optional[str]:
    """
    Display a simple option selector and return selected option
    
    Args:
        console: Rich console for display
        options: List of option strings
        title: Optional title
        instruction: Optional instruction text
        
    Returns:
        Selected option or None if cancelled
    """
    selector = ListSelector(
        console=console,
        items=options,
        mode=SelectionMode.SINGLE,
        title=title,
        instruction=instruction
    )
    
    result = selector.display()
    return result.selected[0] if not result.cancelled and result.selected else None


def select_multiple(console: Console,
                   options: List[str],
                   title: Optional[str] = None,
                   instruction: Optional[str] = None,
                   pre_selected: Optional[List[int]] = None) -> List[str]:
    """
    Display a multiple selection list and return selected options
    
    Args:
        console: Rich console for display
        options: List of option strings
        title: Optional title
        instruction: Optional instruction text
        pre_selected: Optional list of pre-selected indices (0-based)
        
    Returns:
        List of selected options (empty if cancelled)
    """
    # Convert options to SelectionItems with pre-selection
    items = []
    for i, option in enumerate(options):
        selected = pre_selected is not None and i in pre_selected
        items.append(SelectionItem(
            value=option,
            label=option,
            selected=selected
        ))
    
    selector = ListSelector(
        console=console,
        items=items,
        mode=SelectionMode.MULTIPLE,
        title=title,
        instruction=instruction
    )
    
    result = selector.display()
    return result.selected if not result.cancelled else []