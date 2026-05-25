from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class StepIn(_Base):
    key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    role_required: str | None = Field(default=None, max_length=64)
    sla_hours: int | None = Field(default=None, ge=1)

class DefinitionIn(_Base):
    customer_id: str = Field(min_length=1, max_length=64)
    key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    steps: list[StepIn] = []

class DefinitionOut(_Base):
    id: str
    tenant_id: str
    customer_id: str
    key: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

class InstanceIn(_Base):
    customer_id: str = Field(min_length=1, max_length=64)
    definition_key: str = Field(min_length=1, max_length=64)
    entity_ref: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any] = {}
    auto_complete_through_key: str | None = Field(default=None, max_length=64)
    auto_complete_reason: str | None = Field(default=None, max_length=512)
    initial_assignee_ref: str | None = Field(default=None, max_length=128)
    avoid_duplicate: bool = True

class InstanceOut(_Base):
    id: str
    tenant_id: str
    customer_id: str
    entity_ref: str
    state: str
    current_step_id: int | None = None
    current_step_name: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    payload: dict[str, Any] = {}
    tasks: list["TaskOut"] = []

class CancelIn(_Base):
    reason: str | None = None

class TaskOut(_Base):
    id: str
    instance_id: str
    step_name: str
    step_order: int
    role_required: str | None = None
    assignee_ref: str | None = None
    state: str
    due_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by_ref: str | None = None
    note: str | None = None

class CompleteTaskIn(_Base):
    completed_by_ref: str
    note: str | None = None

class NotificationOut(_Base):
    id: str
    tenant_id: str
    customer_id: str
    user_ref: str
    event_type: str
    payload: dict[str, Any]
    read_at: datetime | None = None
    created_at: datetime

class CompleteTaskOut(_Base):
    """Envelope returned by POST /api/v1/tasks/{id}/complete."""
    task: TaskOut
    instance_state: str
    current_step_id: int | None = None
    next_task: TaskOut | None = None
    completed: bool


class WebhookEvent(_Base):
    event_type: str
    tenant_id: str
    customer_id: str
    delivery_id: str
    payload: dict[str, Any]
