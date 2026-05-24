class WFEError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class WFEAuthError(WFEError):
    """401 — API key missing, invalid, or revoked."""

class WFENotFoundError(WFEError):
    """404 — Resource does not exist."""

class WFEConflictError(WFEError):
    """409 — Idempotent operation already applied."""

class WFEValidationError(WFEError):
    """422 — Request payload failed WFE schema validation."""

class WFEServerError(WFEError):
    """5xx or timeout — raised after all retries exhausted."""
