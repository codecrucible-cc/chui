# chui/commands/registry.py

from typing import Dict, Type, Optional, List, Set
from ..utilities.validators import CategoryValidator
from .base import BaseCommand
from ..core.errors import CommandError
import logging

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Manages command registration and lookup"""

    def __init__(self):
        self._commands: Dict[str, Type[BaseCommand]] = {}
        self._categories: Dict[str, List[str]] = {}
        self.validator = CategoryValidator()

        # Initialize core categories
        for category in self.validator.core_categories:
            self._categories[category] = []

    def add_category(self, category: str) -> bool:
        """
        Add a new command category

        Args:
            category: Category name to add

        Returns:
            bool: True if category was added successfully
        """
        if self.validator.add_category(category):
            if category not in self._categories:
                self._categories[category] = []
            return True
        return False

    def register(self, name: str, command_class: Type[BaseCommand],
                 category: str = 'general') -> None:
        """
        Register a command with category validation

        Args:
            name: Command name to register
            command_class: Command class to register
            category: Category to register command under
        """
        if name in self._commands:
            raise CommandError(f"Command {name} is already registered")

        # Check category validity
        if not self.validator.is_valid_category(category):
            logger.warning(
                f"Command {name} using non-standard category: {category}. "
                f"Available categories: {', '.join(sorted(self.validator.get_all_categories()))}"
            )
            # Auto-create category if it passes name validation
            if self.validator.validate_category_name(category):
                self.add_category(category)
            else:
                category = 'general'  # Fallback to general category
                logger.warning(f"Invalid category name. Registering {name} under 'general' category")

        # Ensure category exists in registry
        if category not in self._categories:
            self._categories[category] = []

        # Register command
        self._commands[name] = command_class
        self._categories[category].append(name)

    def get_command(self, name: str) -> Optional[Type[BaseCommand]]:
        """Get a command by name"""
        return self._commands.get(name)

    def get_category_commands(self, category: str) -> List[str]:
        """Get all commands in a category"""
        return self._categories.get(category, []).copy()

    def get_all_categories(self) -> Set[str]:
        """Get all registered categories"""
        return self.validator.get_all_categories()

    def unregister(self, name: str) -> None:
        """Unregister a command"""
        if name in self._commands:
            command_class = self._commands[name]
            del self._commands[name]

            # Remove from categories
            for category in self._categories.values():
                if name in category:
                    category.remove(name)