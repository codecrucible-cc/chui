# chui/utilities/system.py

import os
import platform
import shutil
from pathlib import Path
import sys
import signal
import locale
import subprocess
from typing import Optional, Union, Tuple, Dict, List, Callable
from datetime import datetime
import threading
import tempfile

class PathManager:
    """
    Cross-platform path management utility that ensures consistent behavior
    across different operating systems while leveraging Path objects.
    """

    def __init__(self, app_name: str = "chui"):
        self.app_name = app_name
        self.system = platform.system().lower()
        self._setup_base_paths()

    def _setup_base_paths(self) -> None:
        """Initialize standard application paths based on OS conventions"""
        if self.system == 'windows':
            self.config_home = Path(os.environ.get('APPDATA', '~')).expanduser()
            self.cache_home = Path(os.environ.get('LOCALAPPDATA', '~/.cache')).expanduser()
            self.data_home = self.config_home
        elif self.system == 'darwin':
            self.config_home = Path('~/Library/Application Support').expanduser()
            self.cache_home = Path('~/Library/Caches').expanduser()
            self.data_home = self.config_home
        else:  # Linux and other Unix-like
            self.config_home = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')).expanduser()
            self.cache_home = Path(os.environ.get('XDG_CACHE_HOME', '~/.cache')).expanduser()
            self.data_home = Path(os.environ.get('XDG_DATA_HOME', '~/.local/share')).expanduser()

        # Application-specific paths
        self.app_config_dir = self.config_home / self.app_name
        self.app_cache_dir = self.cache_home / self.app_name
        self.app_data_dir = self.data_home / self.app_name

    def ensure_app_dirs(self) -> None:
        """Ensure all application directories exist with correct permissions"""
        for dir_path in (self.app_config_dir, self.app_cache_dir, self.app_data_dir):
            dir_path.mkdir(parents=True, exist_ok=True)
            if self.system != 'windows':
                dir_path.chmod(0o700)  # Secure permissions on Unix-like systems

    def get_config_file(self, filename: str) -> Path:
        """Get full path for a configuration file"""
        return self.app_config_dir / filename

    def get_cache_file(self, filename: str) -> Path:
        """Get full path for a cache file"""
        return self.app_cache_dir / filename

    def get_data_file(self, filename: str) -> Path:
        """Get full path for a data file"""
        return self.app_data_dir / filename

    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """Convert path to absolute Path object with expanded user"""
        return Path(path).expanduser().resolve()

    def backup_file(self, file_path: Union[str, Path], max_backups: int = 5) -> Optional[Path]:
        """
        Create a backup of a file with timestamp, maintaining limited backups

        Args:
            file_path: Path to file to backup
            max_backups: Maximum number of backups to keep

        Returns:
            Path to backup file if created, None if source doesn't exist
        """
        file_path = self.normalize_path(file_path)
        if not file_path.exists():
            return None

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_name(
            f"{file_path.stem}_{timestamp}{file_path.suffix}.bak"
        )

        # Create backup
        shutil.copy2(file_path, backup_path)

        # Clean up old backups
        backups = sorted(
            file_path.parent.glob(f"{file_path.stem}_*{file_path.suffix}.bak")
        )
        for old_backup in backups[:-max_backups]:
            old_backup.unlink()

        return backup_path


class TerminalManager:
    """
    Cross-platform terminal management utility that provides consistent
    interface for terminal operations while respecting OS differences.
    """

    def __init__(self):
        self.system = platform.system().lower()
        self._setup_terminal_info()

    def _setup_terminal_info(self) -> None:
        """Initialize terminal information and capabilities"""
        # Detect color support
        self.has_color = (
                'COLORTERM' in os.environ or
                os.environ.get('TERM', '').endswith('-256color')
        )

        # Detect if we're in an interactive terminal
        self.is_interactive = os.isatty(sys.stdout.fileno())

        # Get terminal size
        self.size = self.get_terminal_size()

        # Determine default system editor
        self.default_editor = os.environ.get('EDITOR',
                                             'notepad' if self.system == 'windows' else 'vim'
                                             )

    def get_terminal_size(self) -> Tuple[int, int]:
        """
        Get terminal size (columns, lines) with fallback values

        Returns:
            Tuple of (columns, lines)
        """
        try:
            size = os.get_terminal_size()
            return (size.columns, size.lines)
        except (OSError, AttributeError):
            return (80, 24)  # Standard fallback size

    def clear_screen(self) -> None:
        """Clear the terminal screen in an OS-appropriate way"""
        if self.system == 'windows':
            os.system('cls')
        else:
            os.system('clear')

    def get_editor_command(self, filename: str) -> list:
        """
        Get appropriate editor command for the current system

        Args:
            filename: File to edit

        Returns:
            List of command components ready for subprocess
        """
        editor = os.environ.get('EDITOR') or self.default_editor
        if self.system == 'windows' and editor == 'notepad':
            return ['notepad.exe', filename]
        return [editor, filename]

    @property
    def terminal_type(self) -> str:
        """Get the current terminal type"""
        return os.environ.get('TERM', 'dumb')

    def supports_unicode(self) -> bool:
        """Check if terminal supports Unicode"""
        try:
            return sys.stdout.encoding.lower().startswith('utf')
        except AttributeError:
            return False


class ProcessManager:
    """
    Cross-platform process management and execution
    """

    def __init__(self):
        self.system = platform.system().lower()
        self._running_processes: Dict[int, subprocess.Popen] = {}

    def execute(self,
                command: Union[str, List[str]],
                shell: bool = False,
                env: Optional[Dict[str, str]] = None,
                cwd: Optional[Union[str, Path]] = None,
                timeout: Optional[float] = None) -> subprocess.CompletedProcess:
        """
        Execute a command with consistent behavior across platforms

        Args:
            command: Command to execute (string or list)
            shell: Whether to use shell execution
            env: Environment variables
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            CompletedProcess instance
        """
        # Handle Windows-specific command modifications
        if self.system == 'windows':
            if isinstance(command, str) and not shell:
                command = command.split()
            if isinstance(command, list):
                # Convert forward slashes to backslashes in paths
                command = [str(Path(arg)) if '/' in arg else arg for arg in command]

        return subprocess.run(
            command,
            shell=shell,
            env=env,
            cwd=cwd,
            timeout=timeout,
            text=True,
            capture_output=True
        )

    def create_daemon(self, target: Callable, *args, **kwargs) -> threading.Thread:
        """Create a daemon thread that works consistently across platforms"""
        thread = threading.Thread(target=target, args=args, kwargs=kwargs)
        thread.daemon = True
        return thread


class SignalHandler:
    """
    Cross-platform signal handling
    """

    def __init__(self):
        self.system = platform.system().lower()
        self._handlers: Dict[signal.Signals, List[Callable]] = {}
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Setup platform-appropriate signal handling"""
        # Common signals across platforms
        self.SIGINT = signal.SIGINT
        self.SIGTERM = signal.SIGTERM

        # Platform-specific signals
        if self.system != 'windows':
            self.SIGHUP = signal.SIGHUP
            self.SIGQUIT = signal.SIGQUIT

    def register(self, sig: signal.Signals, handler: Callable) -> None:
        """Register a signal handler"""
        if sig not in self._handlers:
            self._handlers[sig] = []
        self._handlers[sig].append(handler)

        def wrapper(signum, frame):
            for h in self._handlers[sig]:
                h()

        signal.signal(sig, wrapper)


class LocaleManager:
    """
    Cross-platform locale and encoding management
    """

    def __init__(self):
        self.system = platform.system().lower()
        self._setup_locale()

    def _setup_locale(self) -> None:
        """Setup proper locale for the system"""
        try:
            # Try to use UTF-8 locale
            if self.system == 'windows':
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            else:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            # Fallback to system default
            locale.setlocale(locale.LC_ALL, '')

    @property
    def encoding(self) -> str:
        """Get system encoding"""
        return locale.getpreferredencoding()

    def encode(self, text: str) -> bytes:
        """Encode text using system encoding"""
        return text.encode(self.encoding, errors='replace')

    def decode(self, bytes_: bytes) -> str:
        """Decode bytes using system encoding"""
        return bytes_.decode(self.encoding, errors='replace')


class TempFileManager:
    """
    Cross-platform temporary file management
    """

    def __init__(self, prefix: str = "chui_"):
        self.prefix = prefix
        self.system = platform.system().lower()
        self._temp_files: List[Path] = []

    @property
    def temp_dir(self) -> Path:
        """Get the application's temporary directory"""
        temp_base = Path(tempfile.gettempdir()) / self.prefix.rstrip('_')
        temp_base.mkdir(parents=True, exist_ok=True)
        return temp_base

    def get_temp_dir(self) -> Path:
        """Get the application's temporary directory"""
        return self.temp_dir

    def create_temp_file(self,
                         suffix: Optional[str] = None,
                         content: Optional[Union[str, bytes]] = None) -> Path:
        """Create a temporary file with optional content"""
        with tempfile.NamedTemporaryFile(
                prefix=self.prefix,
                suffix=suffix,
                delete=False
        ) as tf:
            if content:
                if isinstance(content, str):
                    content = content.encode('utf-8')
                tf.write(content)
                tf.flush()
            temp_path = Path(tf.name)
            self._temp_files.append(temp_path)
            return temp_path

    def cleanup(self) -> None:
        """Remove all temporary files"""
        for temp_file in self._temp_files:
            try:
                temp_file.unlink()
            except FileNotFoundError:
                pass
        self._temp_files.clear()


class NetworkManager:
    """
    Cross-platform network operations
    """

    def __init__(self):
        self.system = platform.system().lower()

    def get_hostname(self) -> str:
        """Get system hostname"""
        return platform.node()

    def is_port_available(self, port: int, host: str = 'localhost') -> bool:
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except socket.error:
                return False

    def get_local_ip(self) -> str:
        """Get local IP address"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                # Doesn't actually connect
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
            except Exception:
                return '127.0.0.1'
