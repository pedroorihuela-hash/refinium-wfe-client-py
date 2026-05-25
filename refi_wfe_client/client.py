from __future__ import annotations
import time
import logging
from typing import Any
import httpx
from .exceptions import (
    WFEAuthError, WFEConflictError, WFEError,
    WFENotFoundError, WFEServerError, WFEValidationError,
)
from .models import (
    CancelIn, CompleteTaskIn, DefinitionIn, InstanceIn,
    InstanceOut, StepIn, TaskOut,
)

log = logging.getLogger(__name__)
_RETRY_DELAYS = [1, 4, 15]

class WFEClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0, retries: int = 3):
        self._base = base_url.rstrip("/")
        self._retries = retries
        self._http = httpx.Client(
            base_url=self._base,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def register_definition(
        self,
        customer_id: str,
        key: str,
        name: str,
        steps: list[dict[str, Any]],
        description: str | None = None,
    ) -> None:
        payload = DefinitionIn(
            customer_id=customer_id, key=key, name=name,
            description=description, steps=[StepIn(**s) for s in steps],
        )
        self._request("POST", "/api/v1/definitions", json=payload.model_dump())
        log.debug("WFE definition registered: customer=%s key=%s", customer_id, key)

    def start_instance(
        self,
        customer_id: str,
        key: str,
        entity_ref: str,
        title: str | None = None,
        payload: dict[str, Any] | None = None,
        auto_complete_through_key: str | None = None,
        auto_complete_reason: str | None = None,
        initial_assignee_ref: str | None = None,
        avoid_duplicate: bool = True,
    ) -> InstanceOut:
        body = InstanceIn(
            customer_id=customer_id,
            definition_key=key,
            entity_ref=entity_ref,
            title=title or f"{key} for {entity_ref}",
            payload=payload or {},
            auto_complete_through_key=auto_complete_through_key,
            auto_complete_reason=auto_complete_reason,
            initial_assignee_ref=initial_assignee_ref,
            avoid_duplicate=avoid_duplicate,
        )
        data = self._request("POST", "/api/v1/instances", json=body.model_dump())
        log.debug("WFE instance started: id=%s entity=%s", data.get("id"), entity_ref)
        return InstanceOut(**data)

    def complete_task(
        self,
        task_id: str,
        completed_by_ref: str,
        note: str | None = None,
    ) -> TaskOut:
        body = CompleteTaskIn(completed_by_ref=completed_by_ref, note=note)
        data = self._request(
            "POST", f"/api/v1/tasks/{task_id}/complete",
            json=body.model_dump(),
        )
        log.debug("WFE task completed: task=%s by=%s", task_id, completed_by_ref)
        return TaskOut(**data)

    def get_tasks(
        self,
        customer_id: str,
        assignee_ref: str | None = None,
        role_ref: str | None = None,
    ) -> list[TaskOut]:
        params: dict[str, str] = {"customer_id": customer_id}
        if assignee_ref:
            params["assignee_ref"] = assignee_ref
        if role_ref:
            params["role_ref"] = role_ref
        data = self._request("GET", "/api/v1/tasks", params=params)
        items = data.get("items", data) if isinstance(data, dict) else data
        return [TaskOut(**t) for t in items]

    def get_instance(self, instance_id: str) -> InstanceOut:
        data = self._request("GET", f"/api/v1/instances/{instance_id}")
        return InstanceOut(**data)

    def cancel_instance(self, instance_id: str, reason: str | None = None) -> None:
        body = CancelIn(reason=reason)
        self._request(
            "POST", f"/api/v1/instances/{instance_id}/cancel",
            json=body.model_dump(),
        )
        log.debug("WFE instance cancelled: id=%s", instance_id)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WFEClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _request(
        self, method: str, path: str, *,
        json: dict | None = None, params: dict | None = None,
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self._retries):
            try:
                resp = self._http.request(method, path, json=json, params=params)
                return self._handle_response(resp)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < self._retries - 1:
                    delay = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)]
                    log.warning("WFE %s %s attempt %d/%d failed — retrying in %ds",
                                method, path, attempt + 1, self._retries, delay)
                    time.sleep(delay)
        raise WFEServerError(
            f"WFE {method} {path} failed after {self._retries} attempts: {last_exc}")

    @staticmethod
    def _handle_response(resp: httpx.Response) -> Any:
        if resp.status_code == 401:
            raise WFEAuthError("WFE auth failed — check WFE_API_KEY", 401)
        if resp.status_code == 404:
            raise WFENotFoundError(f"WFE resource not found: {resp.url}", 404)
        if resp.status_code == 409:
            raise WFEConflictError("WFE conflict — already exists", 409)
        if resp.status_code == 422:
            raise WFEValidationError(f"WFE validation error: {resp.text}", 422)
        if resp.status_code >= 500:
            raise WFEServerError(
                f"WFE server error {resp.status_code}: {resp.text}", resp.status_code)
        if not resp.is_success:
            raise WFEError(
                f"WFE unexpected status {resp.status_code}: {resp.text}", resp.status_code)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()
