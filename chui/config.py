# config.py
import locale
import os
import yaml
import shutil
import logging
import platform
import base64
import getpass
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypedDict, List
from rich.console import Console
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import ui
from .core.errors import ConfigError, ConfigEncryptionError, ErrorCategory
from .utilities.system import (
    PathManager,
    TerminalManager,
    ProcessManager,
    SignalHandler,
    LocaleManager,
    TempFileManager,
    NetworkManager
)


class SystemConfig(TypedDict):
    """Type definition for system configuration"""
    editor: str
    terminal: str
    debug: bool
    log_level: str
    show_banner: bool
    history_size: int
    backup_count: int
    encoding: str
    locale: str
    temp_dir: str
    hostname: str
    platform: str
    is_windows: bool
    is_macos: bool
    is_linux: bool
    has_color: bool
    supports_unicode: bool
    terminal_type: str
    terminal_size: Dict[str, int]


class ConfigUI:
    """Configuration UI utilities"""

    def __init__(self, config, ui):
        self.config = config
        self.ui = ui

    def _format_setting_value(self, value: Any, default_value: Any) -> str:
        """Format setting value for display, indicating if it's default"""
        if value == default_value:
            return f"{str(value)} (default)"
        return str(value)

    def _parse_setting_value(self, value: str, current_value: Any) -> Any:
        """Parse setting value based on current type"""
        # Handle empty input for default
        if not value.strip():
            return None  # Signal to use default

        if isinstance(current_value, bool):
            if value.lower() in ['true', '1', 'yes', 'y']:
                return True
            if value.lower() in ['false', '0', 'no', 'n']:
                return False
            raise ValueError("Boolean value must be true/false, yes/no, or 1/0")
        if isinstance(current_value, int):
            return int(value)
        if isinstance(current_value, float):
            return float(value)
        return value

    def show_settings(self) -> None:
        """Display interactive settings table"""
        from rich.table import Table
        from rich.text import Text

        def format_value(value: Any, default_value: Any) -> Text:
            """Format value with color and default indication"""
            is_default = value == default_value
            if isinstance(value, bool):
                color = "green" if value else "red"
                text = f"{str(value).lower()}"
                if is_default:
                    text += " (default)"
                return Text(text, style=f"bold {color}")

            text = str(value)
            if is_default:
                text += " (default)"
            return Text(text, style="dim" if is_default else "")

        def create_section_table(section: str, config: dict) -> Table:
            table = Table(title=f"{section.title()} Settings", show_header=True)
            table.add_column("Setting", style="cyan")
            table.add_column("Full Path", style="dim")
            table.add_column("Value", style="magenta")
            table.add_column("Actions", style="blue")

            for key, value in sorted(config.items()):
                if isinstance(value, dict):
                    continue

                setting_path = f"{section}.{key}"
                default_value = self.config._get_default(setting_path)
                is_default = value == default_value

                # Always show edit, show reset if not default
                actions = "[link=edit:{setting_path}]edit[/link]"
                if not is_default:
                    actions += " | [link=default:{setting_path}]reset[/link]"

                table.add_row(
                    key,
                    setting_path,
                    format_value(value, default_value),
                    actions
                )

            return table

        # Create tables for each section
        for section, settings in sorted(self.config._config.items()):
            if isinstance(settings, dict):
                table = create_section_table(section, settings)
                self.ui.console.print(table)
                self.ui.console.print()  # Add spacing between sections

    def edit_setting(self, setting_key: str) -> None:
        """Interactive setting editor"""
        current_value = self.config.get(setting_key)
        default_value = self.config._get_default(setting_key)

        if current_value is None:
            self.ui.error(f"Setting not found: {setting_key}")
            return

        # Show current and default values
        self.ui.info(f"Editing: {setting_key}")
        self.ui.info(f"Current value: {self._format_setting_value(current_value, default_value)}")
        self.ui.info(f"Default value: {default_value}")
        self.ui.info("(Press Enter with no value to reset to default)")

        while True:
            try:
                new_value = self.ui.prompt(
                    "Enter new value (or 'cancel' to abort)",
                    default=""
                )
                if new_value.lower() == 'cancel':
                    self.ui.info("Edit cancelled")
                    break

                if not new_value.strip():
                    # Reset to default
                    self.config.reset(setting_key)
                    self.ui.success(f"Reset {setting_key} to default: {default_value}")
                    break

                # Parse and validate the new value
                parsed_value = self._parse_setting_value(new_value, current_value)
                if parsed_value is not None:  # None means use default
                    self.config.set(setting_key, parsed_value)
                    self.ui.success(f"Updated {setting_key} = {parsed_value}")
                break
            except ValueError as e:
                self.ui.error(f"Invalid value: {str(e)}")

    def set_to_default(self, setting_key: str) -> None:
        """Reset a setting to its default value"""
        if not self.config.get(setting_key):
            self.ui.error(f"Setting not found: {setting_key}")
            return

        self.config.reset(setting_key)
        default_value = self.config._get_default(setting_key)
        self.ui.success(f"Reset {setting_key} to default: {default_value}")


class EncryptedValue:
    """Wrapper for encrypted configuration values"""

    def __init__(self, encrypted_value: str):
        self.encrypted_value = encrypted_value

    def __repr__(self):
        return f"<EncryptedValue>"


class Config:
    """Enhanced configuration management with platform-specific defaults and system utilities"""

    def __init__(self, app_name: str = "chui"):
        self.app_name = app_name
        self.console = Console()

        self.error_handler = getattr(ui, 'cmd').error_handler if hasattr(ui, 'cmd') else None

        # Initialize system utilities
        self.path_manager = PathManager(app_name)
        self.terminal = TerminalManager()
        self.process = ProcessManager()
        self.signals = SignalHandler()
        self.locale = LocaleManager()
        self.tempfiles = TempFileManager()
        self.network = NetworkManager()

        # Initialize system information
        self._init_system_info()

        # Initialize configuration
        self._config: Dict = {}
        self._setup_directories()
        self._load_config()

        # Initialize config UI
        self.ui = None  # Will be set by CLI
        self.settings_ui = None

        # Setup logging
        self._setup_logging()

    def _init_system_info(self) -> None:
        """Initialize system-specific information"""
        self.system_info = {
            'platform': self.process.system,
            'is_windows': self.process.system == 'windows',
            'is_macos': self.process.system == 'darwin',
            'is_linux': self.process.system == 'linux',
            'hostname': self.network.get_hostname(),
            'terminal_type': self.terminal.terminal_type,
            'has_color': self.terminal.has_color,
            'supports_unicode': self.terminal.supports_unicode(),
            'encoding': self.locale.encoding,
            'terminal_size': {
                'columns': self.terminal.get_terminal_size()[0],
                'lines': self.terminal.get_terminal_size()[1]
            }
        }

    def reset_all(self, include_plugins: bool = False) -> None:
        """Reset all configuration to defaults, optionally including plugins

        Args:
            include_plugins: Whether to also reset plugin configurations
        """
        try:
            # Get fresh default config
            default_config = self._get_dynamic_config()

            if not include_plugins:
                # Preserve plugin configuration
                default_config['plugins'] = self._config.get('plugins', {})

            # Backup current config
            self._backup_config()

            # Reset to defaults
            self._config = default_config
            self.save()

            # Log the reset
            self.logger.info(
                "Complete config reset performed",
                extra={
                    "include_plugins": include_plugins,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            raise ConfigError(f"Failed to reset configuration: {str(e)}")

    def reset_section(self, section: str) -> None:
        """Reset a specific configuration section to defaults

        Args:
            section: Section name to reset
        """
        try:
            # Get default values for section
            default_config = self._get_dynamic_config()

            if section not in default_config:
                raise ConfigError(f"Invalid configuration section: {section}")

            # Don't allow resetting debug flags
            if section == 'debug':
                raise ConfigError("Cannot reset debug flags - they are read-only system values")

            # Backup current config
            self._backup_config()

            # Reset section to defaults
            self._config[section] = default_config[section]
            self.save()

            # Log the reset
            self.logger.info(
                f"Configuration section '{section}' reset to defaults",
                extra={"section": section, "timestamp": datetime.now().isoformat()}
            )

        except Exception as e:
            raise ConfigError(f"Failed to reset section {section}: {str(e)}")
    def is_debug_flag(self, key_path: str) -> bool:
        """Check if a setting is an immutable debug flag"""
        return key_path.startswith('debug.')
    def _get_dynamic_config(self) -> Dict[str, Any]:
        """Get dynamic configuration based on current system state"""
        terminal_size = self.terminal.get_terminal_size()

        return {
            'system': {
                'editor': self.terminal.default_editor,
                'terminal': self.terminal.terminal_type,
                'debug': False,
                'log_level': 'INFO',
                'show_banner': True,
                'history_size': 1000,
                'backup_count': 3,
                'encoding': self.locale.encoding,
                'locale': locale.getdefaultlocale()[0],
                'temp_dir': str(self.tempfiles.temp_dir),
            },
            'ui': {
                'theme': 'default',
                'color_scheme': 'dark' if self.terminal.has_color else 'none',
                'show_timestamps': True,
                'datetime_format': '%Y-%m-%d %H:%M:%S',
                'prompt_string': 'chui> ',
                'use_unicode': self.terminal.supports_unicode(),
                'terminal_width': terminal_size[0],
                'terminal_height': terminal_size[1],
            },
            'paths': {
                'app_dir': str(self.path_manager.app_data_dir),
                'config_dir': str(self.path_manager.app_config_dir),
                'cache_dir': str(self.path_manager.app_cache_dir),
                'log_file': str(self.path_manager.get_data_file('chui.log')),
                'history_file': str(self.path_manager.get_data_file('history')),
                'plugins_dir': str(self.path_manager.get_data_file('plugins')),
            },
            'plugins': {
                'enabled': [],
                'disabled': [],
                'auto_load': True,
                'paths': [str(self.path_manager.get_data_file('plugins'))]
            },
            'debug': {  # New immutable debug flags section
                'system': {
                    'hostname': platform.node(),
                    'platform': platform.system().lower(),
                    'is_windows': platform.system().lower() == 'windows',
                    'is_macos': platform.system().lower() == 'darwin',
                    'is_linux': platform.system().lower() == 'linux',
                    'python_version': platform.python_version(),
                    'processor': platform.processor(),
                    'machine': platform.machine(),
                    'release': platform.release(),
                    'version': platform.version()
                },
                'terminal': {
                    'has_color': self.terminal.has_color,
                    'supports_unicode': self.terminal.supports_unicode(),
                    'terminal_type': self.terminal.terminal_type,
                    'columns': terminal_size[0],
                    'lines': terminal_size[1],
                    'encoding': self.locale.encoding
                },
                'network': {
                    'hostname': self.network.get_hostname(),
                    'local_ip': self.network.get_local_ip()
                }
            }
        }

    def get_plugin_config_paths(self) -> List[str]:
        """Get list of all plugin configuration paths"""
        plugin_paths = []
        for key in self._config.keys():
            if key not in self._get_dynamic_config():
                # This is likely a plugin config section
                plugin_paths.append(key)
        return plugin_paths

    def validate_config(self, config: Dict) -> None:
        """Validate configuration against expected schema"""
        try:
            SystemConfig(**config['system'])
        except TypeError as e:
            raise ConfigError(f"Invalid system configuration: {str(e)}")

    def init_ui(self, ui) -> None:
        """Initialize UI components"""
        self.ui = ui
        self.settings_ui = ConfigUI(self, ui)

        # Update config based on UI capabilities
        self._config['ui'].update({
            'has_color': ui.capabilities.has_color,
            'is_interactive': ui.capabilities.is_interactive,
            'supports_unicode': ui.capabilities.unicode_support,
            'terminal_width': ui.get_terminal_width()
        })

    def _setup_directories(self) -> None:
        """Ensure all required directories exist"""
        self.path_manager.ensure_app_dirs()

    def _setup_logging(self) -> None:
        """Configure logging based on settings"""
        log_file = self.get('paths.log_file')
        log_level = self.get('system.log_level', 'INFO')

        logging.basicConfig(
            filename=log_file,
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.logger = logging.getLogger(self.app_name)

    def _load_config(self) -> None:
        """Load configuration with fallback to defaults"""
        try:
            config_file = self.path_manager.get_config_file('config.yaml')
            if config_file.exists():
                with open(config_file, 'r', encoding=self.locale.encoding) as f:
                    user_config = yaml.safe_load(f) or {}

                # Get dynamic defaults
                default_config = self._get_dynamic_config()

                # Deep merge with defaults
                self._config = self._deep_merge(default_config, user_config)

                # Backup existing config if it differs from defaults
                if user_config != default_config:
                    self._backup_config()
            else:
                self._config = self._get_dynamic_config()
                self.save()

        except Exception as e:
            self.error_handler.handle(
                error=e,
                category=ErrorCategory.CONFIG,
                operation="load_config",
                context={'config_file': str(config_file)},
                debug=self.get('system.debug', False)
            )
            self._config = self._get_dynamic_config()

    def _backup_config(self) -> None:
        """Create a backup of the current config file"""
        config_file = self.path_manager.get_config_file('config.yaml')
        if config_file.exists():
            self.path_manager.backup_file(
                config_file,
                max_backups=self.get('system.backup_count', 3)
            )

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        merged = base.copy()

        for key, value in update.items():
            if (
                    key in merged and
                    isinstance(merged[key], dict) and
                    isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value

        return merged

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation"""
        try:
            value = self._config
            for key in key_path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any, save: bool = True) -> None:
        """Set a configuration value using dot notation"""
        if self.is_debug_flag(key_path):
            raise ConfigError(f"Cannot modify debug flag: {key_path}")

        # Continue with normal set operation...
        keys = key_path.split('.')
        current = self._config

        # Navigate to the correct location
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

        # Save if requested
        if save:
            self.save()

        # Log the change
        self.logger.debug(f"Config updated: {key_path} = {value}")

    def _get_default(self, key_path: str) -> Any:
        """Get default value for a setting"""
        try:
            default_config = self._get_dynamic_config()
            value = default_config
            for key in key_path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None

    def save(self) -> None:
        """Save current configuration to file"""
        try:
            config_file = self.path_manager.get_config_file('config.yaml')
            with open(config_file, 'w', encoding=self.locale.encoding) as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            self.console.print(f"[red]Error saving config: {str(e)}[/red]")
            self.logger.error(f"Failed to save config: {str(e)}")

    def reset(self, key_path: Optional[str] = None) -> None:
        """Reset configuration to defaults"""
        default_config = self._get_dynamic_config()

        if key_path:
            # Reset specific section
            keys = key_path.split('.')
            default_value = default_config
            try:
                for key in keys:
                    default_value = default_value[key]
                self.set(key_path, default_value)
            except KeyError:
                self.console.print(f"[yellow]No default value for {key_path}[/yellow]")
        else:
            # Reset entire config
            self._config = default_config
            self.save()

        self.logger.info(f"Config reset: {key_path if key_path else 'all'}")

    def update_system_info(self) -> None:
        """Update system information in configuration"""
        self._init_system_info()
        system_config = self._get_dynamic_config()['system']
        self._config['system'].update(system_config)
        self.save()

    def get_encrypted_manager(self) -> 'ConfigEncryptionManager':
        """Get encryption manager for secure values"""
        return ConfigEncryptionManager(self)

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.tempfiles.cleanup()

class ConfigEncryptionManager:
    """Handles encrypted configuration values"""

    def __init__(self, config: Config):
        self.config = config
        self._encryption_key: Optional[bytes] = None
        self.key_file = self.config.path_manager.get_config_file('.key')

    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key for secure storage"""
        if self._encryption_key:
            return self._encryption_key

        try:
            if not self.key_file.exists():
                self._encryption_key = self._create_encryption_key()
            else:
                self._encryption_key = self._load_encryption_key()
            return self._encryption_key
        except Exception as e:
            raise ConfigEncryptionError(
                f"Error with encryption key: {str(e)}",
                operation="key_management"
            )

    def _create_encryption_key(self) -> bytes:
        """Create new encryption key"""
        try:
            # Generate a new key
            salt = os.urandom(16)
            password = self._get_master_password("Create a master password for chui: ")

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Save salt and key
            self.key_file.write_bytes(salt + base64.urlsafe_b64decode(key))
            if not self.config.system_info['is_windows']:
                self.key_file.chmod(0o600)
            return key
        except Exception as e:
            raise ConfigEncryptionError(
                f"Error creating encryption key: {str(e)}",
                operation="create_key"
            )

    def _load_encryption_key(self) -> bytes:
        """Load existing encryption key"""
        try:
            data = self.key_file.read_bytes()
            salt = data[:16]
            stored_key = data[16:]

            password = self._get_master_password("Enter chui master password: ")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            if base64.urlsafe_b64decode(key) != stored_key:
                raise ConfigEncryptionError(
                    "Invalid master password",
                    operation="validate_password"
                )

            return key
        except Exception as e:
            if not isinstance(e, ConfigEncryptionError):
                raise ConfigEncryptionError(
                    f"Error loading encryption key: {str(e)}",
                    operation="load_key"
                )
            raise

    def _get_master_password(self, prompt: str) -> str:
        """Get master password from user"""
        password = getpass.getpass(prompt)
        if not password:
            raise ConfigEncryptionError(
                "Master password cannot be empty",
                operation="get_password"
            )
        return password

    def encrypt_value(self, value: str) -> EncryptedValue:
        """Encrypt a configuration value"""
        try:
            if not self._encryption_key:
                self._encryption_key = self._get_encryption_key()
            f = Fernet(self._encryption_key)
            encrypted = f.encrypt(value.encode()).decode()
            return EncryptedValue(encrypted)
        except Exception as e:
            raise ConfigEncryptionError(
                f"Error encrypting value: {str(e)}",
                operation="encrypt"
            )

    def decrypt_value(self, encrypted: EncryptedValue) -> str:
        """Decrypt a configuration value"""
        try:
            if not self._encryption_key:
                self._encryption_key = self._get_encryption_key()
            f = Fernet(self._encryption_key)
            return f.decrypt(encrypted.encrypted_value.encode()).decode()
        except Exception as e:
            raise ConfigEncryptionError(
                f"Error decrypting value: {str(e)}",
                operation="decrypt"
            )

    def set_encrypted(self, key_path: str, value: str) -> None:
        """Set an encrypted configuration value"""
        encrypted = self.encrypt_value(value)
        self.config.set(key_path, encrypted)

    def get_decrypted(self, key_path: str, default: Any = None) -> Any:
        """Get a decrypted configuration value"""
        value = self.config.get(key_path)
        if isinstance(value, EncryptedValue):
            return self.decrypt_value(value)
        return default

__all__ = [
    'Config',
    'ConfigUI',
    'ConfigEncryptionManager',
    'EncryptedValue',
    'SystemConfig'
]