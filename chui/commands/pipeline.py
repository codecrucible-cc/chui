# commands/pipeline.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID

from chui.events.base import Event


class CommandStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CommandContext:
    """Context for command execution"""
    command_id: UUID
    name: str
    args: List[str]
    options: Dict[str, Any]
    env: Dict[str, str] = field(default_factory=dict)
    cwd: Optional[str] = None
    timeout: Optional[float] = None
    host: Optional[str] = None


@dataclass
class CommandResult:
    """Result of command execution"""
    command_id: UUID
    status: CommandStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommandHook:
    """Hook points for command execution pipeline"""

    def __init__(self):
        self.pre_execute: List[Callable] = []
        self.post_execute: List[Callable] = []
        self.on_error: List[Callable] = []


class CommandPipeline:
    """Manages command execution flow"""

    def __init__(self, event_manager, error_handler):
        self.event_manager = event_manager
        self.error_handler = error_handler
        self.hooks = CommandHook()
        self._active_commands: Dict[UUID, CommandContext] = {}
        self._results: Dict[UUID, CommandResult] = {}

    def register_hook(self, hook_type: str, callback: Callable) -> None:
        """Register a hook for command execution phases"""
        if hook_type == "pre_execute":
            self.hooks.pre_execute.append(callback)
        elif hook_type == "post_execute":
            self.hooks.post_execute.append(callback)
        elif hook_type == "on_error":
            self.hooks.on_error.append(callback)

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute a command with full pipeline processing"""
        # Store active command
        self._active_commands[context.command_id] = context

        result = CommandResult(
            command_id=context.command_id,
            status=CommandStatus.QUEUED,
            start_time=datetime.now()
        )

        try:
            # Run pre-execute hooks
            for hook in self.hooks.pre_execute:
                hook(context)

            # Emit command started event
            self.event_manager.emit(Event(
                name="command.started",
                data={
                    "command_id": str(context.command_id),
                    "command": context.name,
                    "args": context.args,
                    "host": context.host
                },
                timestamp=datetime.now()
            ))

            result.status = CommandStatus.RUNNING

            # Execute command
            if context.host:
                # Remote execution
                result = self._execute_remote(context)
            else:
                # Local execution
                result = self._execute_local(context)

            result.status = CommandStatus.COMPLETED
            result.end_time = datetime.now()

            # Run post-execute hooks
            for hook in self.hooks.post_execute:
                hook(context, result)

            # Emit command completed event
            self.event_manager.emit(Event(
                name="command.completed",
                data={
                    "command_id": str(context.command_id),
                    "exit_code": result.exit_code,
                    "duration": (result.end_time - result.start_time).total_seconds()
                },
                timestamp=datetime.now()
            ))

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.end_time = datetime.now()
            result.error = str(e)

            # Run error hooks
            for hook in self.hooks.on_error:
                hook(context, e)

            # Emit command failed event
            self.event_manager.emit(Event(
                name="command.failed",
                data={
                    "command_id": str(context.command_id),
                    "error": str(e)
                },
                timestamp=datetime.now()
            ))

            # Handle error
            self.error_handler.handle(
                error=e,
                command=context.name,
                host=context.host
            )

        finally:
            # Store result
            self._results[context.command_id] = result
            # Cleanup active command
            del self._active_commands[context.command_id]

        return result

    def _execute_local(self, context: CommandContext) -> CommandResult:
        """Execute command locally on the host system

        This method handles execution of local system commands, applications, and utilities
        such as text editors (vim, notepad), system utilities, or any other host-level
        programs.

        Args:
            context: CommandContext containing command details including:
                    - command_id: Unique identifier for this command execution
                    - name: Command name/executable
                    - args: List of command arguments
                    - options: Additional command options
                    - cwd: Working directory for command execution
                    - env: Environment variables for the command
                    - timeout: Maximum execution time in seconds

        Returns:
            CommandResult containing:
            - command_id: Original command ID
            - status: Final execution status
            - start_time: When command began
            - end_time: When command completed
            - exit_code: Process exit code
            - output: Command output if any
            - error: Error message if failed

        Examples:
            - Opening files in text editor: vim /path/to/file
            - Running system utilities: ls -la, dir, systeminfo
            - Launching local applications: calculator, notepad
        """
        import subprocess
        import time

        result = CommandResult(
            command_id=context.command_id,
            status=CommandStatus.RUNNING,
            start_time=datetime.now()
        )

        try:
            # Prepare command
            cmd = [context.name] + context.args if context.args else [context.name]

            # Execute with subprocess
            process = subprocess.Popen(
                cmd,
                env=context.env,
                cwd=context.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for completion or timeout
            try:
                stdout, stderr = process.communicate(timeout=context.timeout)
                result.exit_code = process.returncode
                result.output = stdout

                if process.returncode != 0:
                    result.status = CommandStatus.FAILED
                    result.error = stderr
                else:
                    result.status = CommandStatus.COMPLETED

            except subprocess.TimeoutExpired:
                process.kill()
                result.status = CommandStatus.FAILED
                result.error = f"Command timed out after {context.timeout} seconds"
                result.exit_code = -1

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)
            result.exit_code = -1

        finally:
            result.end_time = datetime.now()

        return result

    def _execute_remote(self, context: CommandContext) -> CommandResult:
        """Execute command on a remote system via SSH or other protocol

        This method handles execution of commands on remote systems as part of
        infrastructure management capabilities. It will be expanded to support
        various remote execution protocols and authentication methods.

        Args:
            context: CommandContext containing:
                    - command_id: Unique identifier for this execution
                    - name: Command to execute
                    - args: Command arguments
                    - options: Command options
                    - host: Remote host to execute on
                    - env: Environment variables
                    - timeout: Maximum execution time

        Returns:
            CommandResult containing execution details:
            - command_id: Original command ID
            - status: Final execution status
            - start_time: When command began
            - end_time: When command completed
            - exit_code: Remote process exit code
            - output: Command output if any
            - error: Error message if failed

        Examples:
            Future supported operations:
            - Remote system administration
            - Configuration management
            - Service control
            - File operations
            - Multi-host orchestration

        Notes:
            This is a placeholder implementation. The actual remote execution
            functionality will be implemented as part of the infrastructure
            management features. It will likely support:
            - SSH protocol
            - Windows Remote Management (WinRM)
            - Custom agents
            - Authentication methods (keys, credentials)
            - Secure communication
        """
        result = CommandResult(
            command_id=context.command_id,
            status=CommandStatus.FAILED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            error="Remote execution not yet implemented"
        )

        # TODO: Implement remote execution strategy
        # Planned features:
        # - SSH client integration
        # - WinRM support for Windows hosts
        # - Credential management
        # - Host verification
        # - Connection pooling
        # - Multi-protocol support

        return result

    def get_result(self, command_id: UUID) -> Optional[CommandResult]:
        """Get result for a specific command"""
        return self._results.get(command_id)

    def get_active_commands(self) -> Dict[UUID, CommandContext]:
        """Get currently executing commands"""
        return self._active_commands.copy()

    def cancel_command(self, command_id: UUID) -> None:
        """Cancel a running command"""
        if command_id not in self._active_commands:
            raise ValueError(f"No active command found with id: {command_id}")

        context = self._active_commands[command_id]

        # Create cancelled result
        result = CommandResult(
            command_id=command_id,
            status=CommandStatus.CANCELLED,
            start_time=datetime.now(),
            end_time=datetime.now()
        )

        self._results[command_id] = result
        del self._active_commands[command_id]

        # Emit cancelled event
        self.event_manager.emit(Event(
            name="command.cancelled",
            data={"command_id": str(command_id)},
            timestamp=datetime.now()
        ))
