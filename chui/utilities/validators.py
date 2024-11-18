# chui/utilities/validators.py

from typing import Set, Optional
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    def __init__(self):
        self.patterns = {
            'command': re.compile(r'^[a-zA-Z0-9_-]+$'),
            'path': re.compile(r'^[\w\-\./\\]+$'),
            'option': re.compile(r'^--?[a-zA-Z0-9_-]+$')
        }

    def validate_input(self, input_type: str, value: str) -> bool:
        if pattern := self.patterns.get(input_type):
            return bool(pattern.match(value))
        return False


@dataclass
class CategoryValidator:
    """Validator for command categories"""

    # Core categories that are always available
    core_categories: Set[str] = field(default_factory=lambda: {
        'general',
        'system',
        'plugin'
    })

    # Extended categories added by plugins or configuration
    extended_categories: Set[str] = field(default_factory=set)

    # Pattern for valid category names
    category_pattern: str = r'^[a-z][a-z0-9_-]*$'

    def __post_init__(self):
        self._pattern = re.compile(self.category_pattern)

    def validate_category_name(self, name: str) -> bool:
        """
        Validate category name format

        Args:
            name: Category name to validate

        Returns:
            bool: True if name format is valid
        """
        return bool(self._pattern.match(name))

    def is_valid_category(self, category: str) -> bool:
        """
        Check if category is valid (either core or extended)

        Args:
            category: Category to validate

        Returns:
            bool: True if category is valid
        """
        return category in self.core_categories or category in self.extended_categories

    def add_category(self, category: str) -> bool:
        """
        Add a new valid category

        Args:
            category: Category name to add

        Returns:
            bool: True if category was added, False if invalid format
        """
        if not self.validate_category_name(category):
            logger.warning(f"Invalid category name format: {category}")
            return False

        self.extended_categories.add(category)
        return True

    def remove_category(self, category: str) -> bool:
        """
        Remove a category from extended categories

        Args:
            category: Category to remove

        Returns:
            bool: True if category was removed
        """
        if category in self.core_categories:
            logger.warning(f"Cannot remove core category: {category}")
            return False

        if category in self.extended_categories:
            self.extended_categories.remove(category)
            return True
        return False

    def get_all_categories(self) -> Set[str]:
        """Get all valid categories (core and extended)"""
        return self.core_categories | self.extended_categories