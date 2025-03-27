"""
Form components for CHUI UI system.

This module provides interactive form elements for user input.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import re

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt


class FieldType(Enum):
    """Types of form fields"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PASSWORD = "password"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"


@dataclass
class FieldValidator:
    """Validator for form field input"""
    func: Callable[[Any], bool]
    error_message: str
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value, returning success flag and error message"""
        try:
            if self.func(value):
                return True, None
            else:
                return False, self.error_message
        except Exception:
            return False, self.error_message


@dataclass
class FormField:
    """Configuration for a form field"""
    name: str
    label: str
    field_type: FieldType = FieldType.STRING
    required: bool = True
    default: Any = None
    description: Optional[str] = None
    placeholder: Optional[str] = None
    choices: Optional[List[str]] = None
    validators: List[FieldValidator] = field(default_factory=list)
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    pattern_description: Optional[str] = None
    
    def __post_init__(self):
        """Validate field configuration and add built-in validators"""
        # Validate field configuration
        if self.field_type in (FieldType.CHOICE, FieldType.MULTI_CHOICE) and not self.choices:
            raise ValueError(f"Choices must be provided for field type {self.field_type.value}")
            
        # Add built-in validators
        self._add_builtin_validators()
    
    def _add_builtin_validators(self) -> None:
        """Add built-in validators based on field configuration"""
        # Required validator
        if self.required:
            self.validators.append(FieldValidator(
                lambda v: v is not None and (not isinstance(v, str) or v.strip() != ""),
                "This field is required"
            ))
            
        # Min/max value validators for numeric fields
        if self.field_type in (FieldType.INTEGER, FieldType.FLOAT):
            if self.min_value is not None:
                self.validators.append(FieldValidator(
                    lambda v: v >= self.min_value,
                    f"Value must be at least {self.min_value}"
                ))
                
            if self.max_value is not None:
                self.validators.append(FieldValidator(
                    lambda v: v <= self.max_value,
                    f"Value must be at most {self.max_value}"
                ))
                
        # Pattern validator for string fields
        if self.pattern and self.field_type == FieldType.STRING:
            regex = re.compile(self.pattern)
            self.validators.append(FieldValidator(
                lambda v: bool(regex.match(v)),
                self.pattern_description or f"Value must match pattern: {self.pattern}"
            ))
            
        # Choice validator
        if self.field_type == FieldType.CHOICE and self.choices:
            self.validators.append(FieldValidator(
                lambda v: v in self.choices,
                f"Value must be one of: {', '.join(self.choices)}"
            ))


@dataclass
class FormResult:
    """Result of a form submission"""
    values: Dict[str, Any]
    valid: bool
    errors: Dict[str, List[str]] = field(default_factory=dict)


class FormManager:
    """Manages form rendering and validation"""
    
    def __init__(self, console: Console):
        self.console = console
        
    def display_form(self, 
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
        if title:
            self.console.print(f"[bold]{title}[/bold]\n")
            
        values: Dict[str, Any] = {}
        errors: Dict[str, List[str]] = {}
        
        for field in fields:
            # Display field description if provided
            if field.description:
                self.console.print(f"[dim]{field.description}[/dim]")
                
            # Set up prompt based on field type
            value = None
            field_errors = []
            
            while True:
                try:
                    # Different prompt based on field type
                    if field.field_type == FieldType.BOOLEAN:
                        default = None if field.default is None else bool(field.default)
                        value = Confirm.ask(
                            field.label,
                            default=default
                        )
                    elif field.field_type == FieldType.INTEGER:
                        value = IntPrompt.ask(
                            field.label,
                            default=field.default
                        )
                    elif field.field_type == FieldType.FLOAT:
                        value = FloatPrompt.ask(
                            field.label,
                            default=field.default
                        )
                    elif field.field_type == FieldType.PASSWORD:
                        value = Prompt.ask(
                            field.label,
                            default=field.default,
                            password=True
                        )
                    elif field.field_type == FieldType.CHOICE:
                        # Show choices
                        self.console.print(f"\n{field.label}")
                        for i, choice in enumerate(field.choices, 1):
                            self.console.print(f"  {i}. {choice}")
                            
                        # Get user choice
                        choice_input = Prompt.ask(
                            "Enter choice number",
                            default=str(field.choices.index(field.default) + 1) if field.default in field.choices else None
                        )
                        
                        try:
                            choice_idx = int(choice_input) - 1
                            if 0 <= choice_idx < len(field.choices):
                                value = field.choices[choice_idx]
                            else:
                                raise ValueError()
                        except (ValueError, IndexError):
                            self.console.print("[red]Invalid choice[/red]")
                            continue
                    elif field.field_type == FieldType.MULTI_CHOICE:
                        # Show choices
                        self.console.print(f"\n{field.label}")
                        for i, choice in enumerate(field.choices, 1):
                            self.console.print(f"  {i}. {choice}")
                            
                        # Get user choices
                        choice_input = Prompt.ask(
                            "Enter choice numbers (comma-separated)",
                            default=",".join(str(field.choices.index(c) + 1) for c in field.default) if isinstance(field.default, list) else None
                        )
                        
                        try:
                            choices = []
                            for idx in choice_input.split(","):
                                choice_idx = int(idx.strip()) - 1
                                if 0 <= choice_idx < len(field.choices):
                                    choices.append(field.choices[choice_idx])
                                    
                            value = choices
                        except (ValueError, IndexError):
                            self.console.print("[red]Invalid choice format[/red]")
                            continue
                    else:  # Default to string
                        value = Prompt.ask(
                            field.label,
                            default=field.default
                        )
                        
                    # Validate the value
                    field_errors = []
                    for validator in field.validators:
                        is_valid, error = validator.validate(value)
                        if not is_valid:
                            field_errors.append(error)
                            
                    if field_errors:
                        for error in field_errors:
                            self.console.print(f"[red]{error}[/red]")
                    else:
                        break  # Valid input, move to next field
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Form input cancelled[/yellow]")
                    return FormResult(values={}, valid=False)
                    
            # Store the value
            values[field.name] = value
            if field_errors:
                errors[field.name] = field_errors
                
        # Validate the form as a whole
        valid = len(errors) == 0
                
        return FormResult(
            values=values,
            valid=valid,
            errors=errors
        )


def create_string_field(name: str, 
                       label: str, 
                       required: bool = True, 
                       default: Optional[str] = None,
                       description: Optional[str] = None) -> FormField:
    """Create a string input field"""
    return FormField(
        name=name,
        label=label,
        field_type=FieldType.STRING,
        required=required,
        default=default,
        description=description
    )


def create_password_field(name: str, 
                         label: str, 
                         required: bool = True,
                         description: Optional[str] = None) -> FormField:
    """Create a password input field"""
    return FormField(
        name=name,
        label=label,
        field_type=FieldType.PASSWORD,
        required=required,
        description=description
    )


def create_choice_field(name: str, 
                       label: str, 
                       choices: List[str],
                       required: bool = True, 
                       default: Optional[str] = None,
                       description: Optional[str] = None) -> FormField:
    """Create a choice selection field"""
    return FormField(
        name=name,
        label=label,
        field_type=FieldType.CHOICE,
        required=required,
        default=default,
        choices=choices,
        description=description
    )


def create_boolean_field(name: str, 
                        label: str, 
                        default: Optional[bool] = None,
                        description: Optional[str] = None) -> FormField:
    """Create a boolean input field"""
    return FormField(
        name=name,
        label=label,
        field_type=FieldType.BOOLEAN,
        required=False,  # Booleans are always considered provided
        default=default,
        description=description
    )


def create_number_field(name: str, 
                       label: str, 
                       required: bool = True, 
                       default: Optional[Union[int, float]] = None,
                       field_type: FieldType = FieldType.INTEGER,
                       min_value: Optional[Union[int, float]] = None,
                       max_value: Optional[Union[int, float]] = None,
                       description: Optional[str] = None) -> FormField:
    """Create a numeric input field"""
    return FormField(
        name=name,
        label=label,
        field_type=field_type,
        required=required,
        default=default,
        min_value=min_value,
        max_value=max_value,
        description=description
    )