"""
Text formatters for CHUI UI system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class TextFormatter:
    """Handles formatting of text output for display"""
    
    @staticmethod
    def strip_style_markers(content: str) -> str:
        """Remove style markers from content for plain text output"""
        # Remove rich markup
        content = content.replace('[red]', '')
        content = content.replace('[green]', '')
        content = content.replace('[blue]', '')
        content = content.replace('[yellow]', '')
        content = content.replace('[bold]', '')
        content = content.replace('[italic]', '')
        content = content.replace('[dim]', '')
        content = content.replace('[/]', '')
        content = content.replace('[/red]', '')
        content = content.replace('[/green]', '')
        content = content.replace('[/blue]', '')
        content = content.replace('[/yellow]', '')
        content = content.replace('[/bold]', '')
        content = content.replace('[/italic]', '')
        content = content.replace('[/dim]', '')
        return content
    
    @staticmethod
    def format_timestamp(timestamp: Union[str, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a timestamp for display"""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                return timestamp
        
        if isinstance(timestamp, datetime):
            return timestamp.strftime(format_str)
        
        return str(timestamp)
        
    @staticmethod
    def format_boolean(value: bool, true_text: str = "Yes", false_text: str = "No") -> str:
        """Format a boolean value for display"""
        return true_text if value else false_text
        
    @staticmethod
    def format_list(items: List[Any], separator: str = ", ") -> str:
        """Format a list for display"""
        return separator.join(str(item) for item in items)
        
    @staticmethod
    def format_dict(data: Dict[str, Any], indent: int = 0) -> str:
        """Format a dictionary for display"""
        lines = []
        indent_str = " " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(TextFormatter.format_dict(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}: {TextFormatter.format_list(value)}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
                
        return "\n".join(lines)
        
    @staticmethod
    def truncate_text(text: str, max_length: int, ellipsis: str = "...") -> str:
        """Truncate text to a maximum length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(ellipsis)] + ellipsis
        
    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """Format bytes into a human-readable string"""
        if size_bytes == 0:
            return "0B"
            
        size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
            
        return f"{size_bytes:.2f}{size_names[i]}"