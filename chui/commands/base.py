# commands/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

from .pipeline import CommandContext, CommandResult, CommandStatus
from ..ui import UI
from ..config import Config


class BaseCommand(ABC):
    """Base class for all commands"""

    def __init__(self, ui: UI, config: Config, pipeline=None):
        self.ui = ui
        self.config = config
        self.pipeline = pipeline

    @abstractmethod
    def execute(self, args: List[str], flags: Dict[str, bool],
                options: Dict[str, str]) -> Any:
        """Execute the command"""
        pass

    @property
    @abstractmethod
    def help(self) -> str:
        """Get command help text"""
        pass

    def process_result(self, result: CommandResult) -> Any:
        """Process command execution result"""
        if result.status == CommandStatus.FAILED:
            self.ui.error(f"Command failed: {result.error}")
            return False
        if result.output:
            self.ui.info(result.output)
        return True


class InfrastructureCommand(BaseCommand):
    """Base class for infrastructure-related commands"""

    def execute(self, args: List[str], flags: Dict[str, bool],
                options: Dict[str, str]) -> Any:
        """Execute with infrastructure context"""
        if not self.pipeline:
            raise RuntimeError("Infrastructure commands require a command pipeline")

        # Create command context
        context = CommandContext(
            command_id=uuid4(),
            name=self.__class__.__name__,
            args=args,
            options=options,
            host=options.get('host'),
            env=self.get_environment(flags),
            timeout=float(options.get('timeout', 300))
        )

        # Execute through pipeline
        result = self.pipeline.execute(context)
        return self.process_result(result)

    def get_environment(self, flags: Dict[str, bool]) -> Dict[str, str]:
        """Get command environment based on flags"""
        env = {}
        if flags.get('debug'):
            env['DEBUG'] = '1'
        return env
