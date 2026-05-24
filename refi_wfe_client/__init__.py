"""refi-wfe-client — typed Python SDK for the Refinium AI Platform Workflow Engine."""
__version__ = "0.1.0"

from .client import WFEClient
from .exceptions import (
    WFEAuthError, WFEConflictError, WFEError,
    WFENotFoundError, WFEServerError, WFEValidationError,
)
from .models import (
    DefinitionOut, InstanceOut, NotificationOut, TaskOut, WebhookEvent,
)
from .webhook import verify_webhook_signature

__all__ = [
    "WFEClient",
    "WFEError", "WFEAuthError", "WFENotFoundError",
    "WFEConflictError", "WFEValidationError", "WFEServerError",
    "DefinitionOut", "InstanceOut", "TaskOut", "NotificationOut", "WebhookEvent",
    "verify_webhook_signature",
]
