"""
Terminal capabilities detection and management for CHUI UI system.
"""

import os
import platform
import sys
from typing import Optional


class UICapabilities:
    """Manages UI capabilities and feature detection"""

    def __init__(self):
        self.system = platform.system().lower()
        self.has_color = self._detect_color()
        self.is_interactive = self._detect_interactive()
        self.terminal_size = self._get_terminal_size()
        self.unicode_support = self._detect_unicode()

    def _detect_color(self) -> bool:
        """Detect color support with Windows-specific handling"""
        if self.system == 'windows':
            # Windows 10+ generally supports color
            # Check for known Windows terminals that support color
            if (
                    'WT_SESSION' in os.environ or  # Windows Terminal
                    'TERM_PROGRAM' in os.environ or  # VS Code, etc.
                    os.environ.get('TERM') == 'xterm-256color' or
                    os.environ.get('ANSICON') is not None
            ):
                return True
            # Enable VT100 processing for legacy Windows console
            import ctypes
            kernel32 = ctypes.windll.kernel32
            try:
                # Enable ANSI support in legacy Windows console
                kernel32.SetConsoleMode(
                    kernel32.GetStdHandle(-11),  # STD_OUTPUT_HANDLE
                    7  # ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                )
                return True
            except:
                pass
            return False

        # Unix-like systems
        return (
                'COLORTERM' in os.environ or
                os.environ.get('TERM', '').endswith('-color') or
                os.environ.get('CLICOLOR', '0') == '1'
        )

    def _detect_interactive(self) -> bool:
        """Detect if terminal is interactive"""
        return os.isatty(sys.stdout.fileno())

    def _get_terminal_size(self) -> os.terminal_size:
        """Get terminal size with fallback"""
        try:
            return os.get_terminal_size()
        except OSError:
            return os.terminal_size((80, 24))  # fallback size

    def _detect_unicode(self) -> bool:
        """Detect if terminal supports Unicode"""
        try:
            return sys.stdout.encoding.lower().startswith('utf')
        except AttributeError:
            return False
            
    def get_terminal_width(self) -> int:
        """Get current terminal width"""
        return self.terminal_size.columns
        
    def get_terminal_height(self) -> int:
        """Get current terminal height"""
        return self.terminal_size.lines
        
    def supports_feature(self, feature: str) -> bool:
        """Check if a specific UI feature is supported"""
        return getattr(self, f"has_{feature}", False)