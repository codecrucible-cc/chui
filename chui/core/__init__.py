from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import shlex

@dataclass
class ParsedCommand:
    """Parsed command information"""
    command: str
    args: List[str]
    flags: Dict[str, bool]
    options: Dict[str, str]



class CLIUtils:
    """CLI utility functions"""

    @staticmethod
    def parse_command(cmd_str: str) -> ParsedCommand:
        """Parse command string into components"""
        parts = shlex.split(cmd_str)
        if not parts:
            return ParsedCommand("", [], {}, {})

        command = parts[0]
        args = []
        flags = {}
        options = {}

        i = 1
        while i < len(parts):
            curr = parts[i]

            if curr.startswith('--'):
                # Long option
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    options[curr[2:]] = parts[i + 1]
                    i += 2
                else:
                    flags[curr[2:]] = True
                    i += 1
            elif curr.startswith('-'):
                # Short flag(s)
                for flag in curr[1:]:
                    flags[flag] = True
                i += 1
            else:
                args.append(curr)
                i += 1

        return ParsedCommand(command, args, flags, options)

    @staticmethod
    def format_help(
            description: str,
            usage: str,
            examples: Optional[List[str]] = None
    ) -> str:
        """Format command help text"""
        lines = [description, "", "Usage:", usage]

        if examples:
            lines.extend(["", "Examples:"])
            lines.extend(examples)

        return "\n".join(lines)