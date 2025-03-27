# chui/utilities/aliases.py

from typing import Dict, Any, Optional
from pathlib import Path
import json


class AliasManager:
    """
    Manages persistence of command aliases.
    """
    
    def __init__(self, config):
        self.config = config
        
    def load_aliases(self) -> Dict[str, str]:
        """
        Load aliases from config file
        
        Returns:
            Dictionary of alias name to command mapping
        """
        return self.config.get('aliases', {})
    
    def save_aliases(self, aliases: Dict[str, str]) -> None:
        """
        Save aliases to config file
        
        Args:
            aliases: Dictionary of alias name to command mapping
        """
        self.config.set('aliases', aliases)
        
    def add_alias(self, name: str, command: str) -> None:
        """
        Add a new alias
        
        Args:
            name: Alias name
            command: Command to execute
        """
        aliases = self.load_aliases()
        aliases[name] = command
        self.save_aliases(aliases)
        
    def remove_alias(self, name: str) -> bool:
        """
        Remove an alias
        
        Args:
            name: Alias name to remove
            
        Returns:
            True if alias was removed, False if alias not found
        """
        aliases = self.load_aliases()
        if name in aliases:
            del aliases[name]
            self.save_aliases(aliases)
            return True
        return False

    def get_alias(self, name: str) -> Optional[str]:
        """
        Get command for alias
        
        Args:
            name: Alias name
            
        Returns:
            Command for alias or None if alias not found
        """
        aliases = self.load_aliases()
        return aliases.get(name)
    