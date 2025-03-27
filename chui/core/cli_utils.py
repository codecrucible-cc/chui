import shlex
import json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ParsedCommand:
    """Parsed command information"""
    command: str
    args: List[str]
    flags: Dict[str, bool]
    options: Dict[str, Any]

class CLIUtils:
    """CLI utility functions"""

    @staticmethod
    def _strip_comments(cmd_str: str) -> str:
        """Strip comments from command string
        
        Args:
            cmd_str: Raw command string
            
        Returns:
            Command string with comments removed
        """
        # Handle quoted strings and comments
        result = []
        in_quote = False
        quote_char = None
        i = 0
        
        while i < len(cmd_str):
            char = cmd_str[i]
            
            # Handle quotes
            if char in ['"', "'"]:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                result.append(char)
                
            # Handle comments
            elif char == '#' and not in_quote:
                # Stop processing at comment
                break
                
            # Handle escaped characters
            elif char == '\\' and i + 1 < len(cmd_str):
                result.append(char)
                result.append(cmd_str[i + 1])
                i += 1
                
            else:
                result.append(char)
                
            i += 1
            
        return ''.join(result).strip()

    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string value to appropriate type"""
        # Remove any leading/trailing whitespace
        value = value.strip()
        
        # Handle boolean values
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
            
        # Handle None values
        if value.lower() in ('none', 'null'):
            return None
            
        # Handle numbers
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
            
        # Handle JSON objects
        if value.startswith('{') and value.endswith('}'):
            try:
                # Make sure keys are properly quoted
                if '"' not in value:
                    value = value.replace('{', '{"').replace(':', '":"').replace(',', '","').replace('}', '"}')
                return json.loads(value)
            except:
                pass
                
        # Handle arrays
        if value.startswith('[') and value.endswith(']'):
            try:
                return json.loads(value)
            except:
                pass
                
        # Default to string
        return value.strip('"\'')

    @staticmethod
    def _clean_command(cmd_str: str) -> str:
        """Clean command string by handling line continuations and extra whitespace"""
        # First strip any comments
        cmd_str = CLIUtils._strip_comments(cmd_str)
        
        # Remove line continuation characters and normalize whitespace
        cmd_str = cmd_str.replace('\\\n', ' ').replace('\\', ' ')
        
        # Normalize multiple spaces
        cmd_str = ' '.join(cmd_str.split())
        
        return cmd_str

    @staticmethod
    def parse_command(cmd_str: str) -> ParsedCommand:
        """Parse command string into components with improved handling"""
        # Clean the command string first
        cmd_str = CLIUtils._clean_command(cmd_str)
        
        # Handle empty commands
        if not cmd_str:
            return ParsedCommand("", [], {}, {})
            
        # Split command respecting quotes
        try:
            parts = shlex.split(cmd_str)
        except ValueError as e:
            # Handle unclosed quotes
            parts = cmd_str.split()
            
        if not parts:
            return ParsedCommand("", [], {}, {})
            
        args = []
        flags = {}
        options = {}
        i = 0
        
        while i < len(parts):
            curr = parts[i].strip()
            
            # Handle long options (--option)
            if curr.startswith('--'):
                option_name = curr[2:]
                
                # Handle --option=value format
                if '=' in option_name:
                    name, value = option_name.split('=', 1)
                    options[name.strip()] = CLIUtils._convert_value(value)
                    i += 1
                    continue
                    
                # Handle --flag format (boolean flag)
                if i + 1 >= len(parts) or parts[i + 1].startswith('-'):
                    flags[option_name.strip()] = True
                    i += 1
                    continue
                    
                # Handle --option value format
                if i + 1 < len(parts):
                    options[option_name.strip()] = CLIUtils._convert_value(parts[i + 1])
                    i += 2
                else:
                    flags[option_name.strip()] = True
                    i += 1
                continue
                
            # Handle short options (-o)
            elif curr.startswith('-'):
                if '=' in curr:
                    # Handle -o=value format
                    flag, value = curr[1:].split('=', 1)
                    options[flag.strip()] = CLIUtils._convert_value(value)
                    i += 1
                    continue
                    
                # Handle combined flags (-abc) 
                for flag in curr[1:]:
                    flags[flag] = True
                i += 1
                continue
                
            # Regular argument
            else:
                args.append(curr)
                i += 1
        
        return ParsedCommand("", args, flags, options)