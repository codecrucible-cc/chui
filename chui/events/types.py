# events/types.py

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class InfraEventType(Enum):
    # Host Events
    HOST_CONNECTING = "host.connecting"
    HOST_CONNECTED = "host.connected"
    HOST_CONNECTION_FAILED = "host.connection_failed"
    HOST_DISCONNECTED = "host.disconnected"

    # Deployment Events
    DEPLOY_STARTED = "deploy.started"
    DEPLOY_CONFIG_VALIDATED = "deploy.config_validated"
    DEPLOY_CONFIG_INVALID = "deploy.config_invalid"
    DEPLOY_STEP_STARTED = "deploy.step.started"
    DEPLOY_STEP_COMPLETED = "deploy.step.completed"
    DEPLOY_STEP_FAILED = "deploy.step.failed"
    DEPLOY_COMPLETED = "deploy.completed"
    DEPLOY_FAILED = "deploy.failed"

    # Command Events
    COMMAND_QUEUED = "command.queued"
    COMMAND_STARTED = "command.started"
    COMMAND_OUTPUT = "command.output"
    COMMAND_COMPLETED = "command.completed"
    COMMAND_FAILED = "command.failed"

    # Service Events
    SERVICE_STATUS_CHANGED = "service.status_changed"
    SERVICE_HEALTH_CHECK = "service.health_check"


@dataclass
class HostEventData:
    host: str
    port: int
    user: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class DeployEventData:
    deployment_id: str
    target_hosts: list[str]
    step_name: Optional[str] = None
    config_path: Optional[str] = None
    error_message: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None


@dataclass
class CommandEventData:
    command_id: str
    command: str
    host: str
    exit_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None