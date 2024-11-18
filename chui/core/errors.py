# core/errors.py

import traceback
import logging
from typing import Optional, Type, Dict, Any, Callable
from enum import Enum
from datetime import datetime

from rich.console import Console


class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Categories for different types of errors"""
    CONFIG = "Configuration"
    PLUGIN = "Plugin"
    COMMAND = "Command"
    SYSTEM = "System"
    SECURITY = "Security"
    UI = "Interface"
    NETWORK = "Network"
    FILE = "File System"
    PROCESS = "Process"
    DATABASE = "Database"
    UNKNOWN = "Unknown"
class ErrorContext:
    """Context information for errors"""

    def __init__(self,
                 error: Exception,
                 category: ErrorCategory,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 context: Optional[Dict[str, Any]] = None,
                 operation: Optional[str] = None):
        self.error = error
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.operation = operation
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc() if error else None


class ChuiError(Exception):
    """Base exception class for CHUI framework"""

    def __init__(self,
                 message: str,
                 original_error: Optional[Exception] = None,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.original_error = original_error
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/display"""
        return {
            'type': self.__class__.__name__,
            'message': str(self),
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'original_error': str(self.original_error) if self.original_error else None
        }


class SecurityError(ChuiError):
    """Security-related errors with enhanced context and severity tracking"""

    class ViolationType(Enum):
        """Types of security violations"""
        UNAUTHORIZED_ACCESS = "unauthorized_access"
        INVALID_CREDENTIALS = "invalid_credentials"
        PERMISSION_DENIED = "permission_denied"
        ENCRYPTION_FAILURE = "encryption_failure"
        INTEGRITY_VIOLATION = "integrity_violation"
        SECURE_CHANNEL_FAILURE = "secure_channel_failure"
        CERTIFICATE_ERROR = "certificate_error"
        TOKEN_ERROR = "token_error"
        UNSAFE_OPERATION = "unsafe_operation"
        POLICY_VIOLATION = "policy_violation"

    def __init__(self,
                 message: str,
                 violation_type: ViolationType,
                 operation: Optional[str] = None,
                 user: Optional[str] = None,
                 resource: Optional[str] = None,
                 original_error: Optional[Exception] = None,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize security error with enhanced context

        Args:
            message: Error description
            violation_type: Type of security violation
            operation: Operation being performed when violation occurred
            user: User involved in the security violation
            resource: Resource being accessed
            original_error: Original exception if any
            severity: Error severity level
            context: Additional context information
        """
        context = context or {}
        context.update({
            'violation_type': violation_type.value,
            'operation': operation,
            'user': user,
            'resource': resource,
            'timestamp': datetime.now().isoformat()
        })

        super().__init__(
            message=message,
            original_error=original_error,
            severity=severity,
            context=context
        )

        self.violation_type = violation_type
        self.operation = operation
        self.user = user
        self.resource = resource

    @property
    def requires_audit(self) -> bool:
        """Determine if this security error requires auditing"""
        return self.violation_type in [
            self.ViolationType.UNAUTHORIZED_ACCESS,
            self.ViolationType.INTEGRITY_VIOLATION,
            self.ViolationType.POLICY_VIOLATION
        ]

    @property
    def requires_immediate_action(self) -> bool:
        """Determine if this security error requires immediate action"""
        return self.severity == ErrorSeverity.CRITICAL or self.violation_type in [
            self.ViolationType.INTEGRITY_VIOLATION,
            self.ViolationType.SECURE_CHANNEL_FAILURE
        ]

    def to_audit_log(self) -> Dict[str, Any]:
        """Format error for security audit log"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'violation_type': self.violation_type.value,
            'message': str(self),
            'severity': self.severity.value,
            'operation': self.operation,
            'user': self.user,
            'resource': self.resource,
            'context': self.context,
            'requires_action': self.requires_immediate_action
        }

    def __str__(self) -> str:
        """Enhanced string representation with security context"""
        base_msg = super().__str__()
        context_msg = f" ({self.violation_type.value})"
        if self.operation:
            context_msg += f" during {self.operation}"
        if self.user:
            context_msg += f" by user {self.user}"
        if self.resource:
            context_msg += f" accessing {self.resource}"
        return base_msg + context_msg
class ConfigError(ChuiError):
    """Configuration-related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)


class ConfigEncryptionError(ConfigError):
    """Configuration encryption-related errors"""

    def __init__(self,
                 message: str,
                 operation: Optional[str] = None,
                 key_id: Optional[str] = None,
                 **kwargs):
        context = kwargs.pop('context', {})
        context.update({
            'operation': operation,
            'key_id': key_id
        })
        super().__init__(message, context=context, **kwargs)


class ConfigValidationError(ConfigError):
    """Configuration validation errors"""

    def __init__(self,
                 message: str,
                 validation_errors: Optional[Dict[str, str]] = None,
                 **kwargs):
        context = kwargs.pop('context', {})
        if validation_errors:
            context['validation_errors'] = validation_errors
        super().__init__(message, context=context, **kwargs)


class PluginError(ChuiError):
    """Plugin-related errors"""

    def __init__(self,
                 message: str,
                 plugin_name: Optional[str] = None,
                 **kwargs):
        context = kwargs.pop('context', {})
        if plugin_name:
            context['plugin_name'] = plugin_name
        super().__init__(message, context=context, **kwargs)


class CommandError(ChuiError):
    """Command execution errors"""

    def __init__(self,
                 message: str,
                 command: Optional[str] = None,
                 args: Optional[list] = None,
                 **kwargs):
        context = kwargs.pop('context', {})
        context.update({
            'command': command,
            'args': args
        })
        super().__init__(message, context=context, **kwargs)


class EventError(ChuiError):
    """Event handling related errors"""

    def __init__(self,
                 message: str,
                 event_type: Optional[str] = None,
                 **kwargs):
        context = kwargs.pop('context', {})
        if event_type:
            context['event_type'] = event_type
        super().__init__(message, context=context, **kwargs)


class ErrorHandler:
    """Centralized error handling with enhanced logging and context"""

    def __init__(self, ui, config=None):
        self.ui = ui
        self.config = config
        self.console = Console(stderr=True)
        self.logger = logging.getLogger('chui.errors')

        # Error type mappings with custom handlers
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default error handlers"""
        self.register_handler(ConfigError, self._handle_config_error)
        self.register_handler(PluginError, self._handle_plugin_error)
        self.register_handler(CommandError, self._handle_command_error)
        self.register_handler(SecurityError, self._handle_security_error)
        self.register_handler(SystemError, self._handle_system_error)
        self.register_handler(FileNotFoundError, self._handle_file_error)
        self.register_handler(PermissionError, self._handle_permission_error)

    def register_handler(self,
                         error_type: Type[Exception],
                         handler: Callable) -> None:
        """Register a custom error handler"""
        self._handlers[error_type] = handler

    def handle(self,
               error: Exception,
               category: ErrorCategory = ErrorCategory.UNKNOWN,
               severity: ErrorSeverity = ErrorSeverity.ERROR,
               context: Optional[Dict[str, Any]] = None,
               operation: Optional[str] = None,
               debug: bool = False) -> None:
        """
        Handle an error with appropriate logging and user feedback
        """
        # Create error context
        error_ctx = ErrorContext(
            error=error,
            category=category,  # Make sure this is an ErrorCategory enum
            severity=severity,
            context=context or {},
            operation=operation
        )

        # Log the error
        self._log_error(error_ctx)

        # Find and execute appropriate handler
        handler = self._get_handler(type(error))
        handler(error_ctx)

        # Display debug information if requested
        if debug and error_ctx.traceback:
            self.ui.debug("Traceback:")
            self.ui.debug(error_ctx.traceback)

    def _get_handler(self, error_type: Type[Exception]) -> Callable:
        """Get appropriate handler for error type"""
        for err_type, handler in self._handlers.items():
            if issubclass(error_type, err_type):
                return handler
        return self._handle_generic_error

    def _log_error(self, context: ErrorContext) -> None:
        """Log error with full context"""
        error_dict = {
            'timestamp': context.timestamp.isoformat(),
            'category': context.category.value if hasattr(context.category, 'value') else str(context.category),
            'severity': context.severity.value if hasattr(context.severity, 'value') else str(context.severity),
            'operation': context.operation,
            'error': str(context.error),
            'context': context.context
        }

        if context.traceback:
            error_dict['traceback'] = context.traceback

        log_method = getattr(
            self.logger,
            context.severity.value.lower() if hasattr(context.severity, 'value') else 'error',
            self.logger.error
        )
        log_method(error_dict)

    # Default error handlers
    def _handle_config_error(self, context: ErrorContext) -> None:
        """Handle configuration errors"""
        self.ui.error(f"Configuration error: {context.error}")
        if context.operation:
            self.ui.info(f"While performing: {context.operation}")
        if self.config:
            self.ui.info("Try resetting the affected configuration:")
            self.ui.info(f"  settings reset {context.context.get('setting', '')}")

    def _handle_plugin_error(self, context: ErrorContext) -> None:
        """Handle plugin-related errors"""
        self.ui.error(f"Plugin error: {context.error}")
        plugin_name = context.context.get('plugin_name')
        if plugin_name:
            self.ui.info(f"Affected plugin: {plugin_name}")
            self.ui.info("Try: plugins reload <plugin_name>")

    def _handle_command_error(self, context: ErrorContext) -> None:
        """Handle command execution errors"""
        self.ui.error(f"Command error: {context.error}")
        cmd = context.context.get('command')
        if cmd:
            self.ui.info(f"Failed command: {cmd}")
            self.ui.info("Try 'help <command>' for usage information")

    def _handle_security_error(self, context: ErrorContext) -> None:
        """Handle security-related errors"""
        self.ui.error(f"Security error: {context.error}")
        self.logger.critical(f"Security violation: {context.error}")

    def _handle_system_error(self, context: ErrorContext) -> None:
        """Handle system-related errors"""
        self.ui.error(f"System error: {context.error}")
        if context.context.get('needs_restart'):
            self.ui.warning("This error may require restarting the application")

    def _handle_file_error(self, context: ErrorContext) -> None:
        """Handle file-related errors"""
        self.ui.error(f"File error: {context.error}")
        path = context.context.get('path')
        if path:
            self.ui.info(f"Affected path: {path}")

    def _handle_permission_error(self, context: ErrorContext) -> None:
        """Handle permission-related errors"""
        self.ui.error(f"Permission denied: {context.error}")
        if context.context.get('needs_elevation'):
            self.ui.info("This operation may require elevated privileges")

    def _handle_generic_error(self, context: ErrorContext) -> None:
        """Handle any unrecognized error"""
        self.ui.error(f"Error: {context.error}")