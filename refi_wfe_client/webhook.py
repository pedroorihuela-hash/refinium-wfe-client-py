from __future__ import annotations
import hashlib
import hmac

def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """Return True if signature_header matches HMAC-SHA256 of payload."""
    if not signature_header.startswith("sha256="):
        return False
    expected_hex = signature_header[len("sha256="):]
    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, expected_hex)
