import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import re

# Context variables for global request/job correlation
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="system")
workspace_id_ctx: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)
actor_id_ctx: ContextVar[Optional[str]] = ContextVar("actor_id", default=None)

logger = logging.getLogger("sva.telemetry")

TELEMETRY_SCHEMA_VERSION = "1.0.0"

_SECRET_PATTERNS = [
    re.compile(r"password.*?:.*?(?:\"|'|)([^\"',}]+)", re.IGNORECASE),
    re.compile(r"secret.*?:.*?(?:\"|'|)([^\"',}]+)", re.IGNORECASE),
    re.compile(r"api[_-]?key.*?:.*?(?:\"|'|)([^\"',}]+)", re.IGNORECASE),
    re.compile(r"token.*?:.*?(?:\"|'|)([^\"',}]+)", re.IGNORECASE),
    re.compile(r"(ghp|glpat)_[a-zA-Z0-9_]+", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE)
]

def scrub_secrets(data: Any) -> Any:
    """Recursively scrub secrets from telemetry payloads."""
    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ("password", "secret", "token", "api_key", "credential", "private_key", "access_key")):
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = scrub_secrets(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_secrets(item) for item in data]
    elif isinstance(data, str):
        scrubbed_str = data
        for pattern in _SECRET_PATTERNS:
            scrubbed_str = pattern.sub(r"\g<0> [REDACTED]", scrubbed_str)
            # A more robust regex replacement for specific formats
            if "ghp_" in scrubbed_str or "glpat_" in scrubbed_str:
                scrubbed_str = re.sub(r"(ghp|glpat)_[a-zA-Z0-9_]+", "[REDACTED_TOKEN]", scrubbed_str)
            if "Bearer " in scrubbed_str:
                scrubbed_str = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer [REDACTED]", scrubbed_str)
        return scrubbed_str
    return data

class TelemetryLogger:
    @staticmethod
    def log_event(
        event_type: str,
        details: Dict[str, Any],
        outcome: str = "SUCCESS",
        error_class: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """Log a structured telemetry event adhering to Phase 18D schema."""
        event = {
            "schema_version": TELEMETRY_SCHEMA_VERSION,
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id_ctx.get(),
            "workspace_id": workspace_id_ctx.get(),
            "actor_id": actor_id_ctx.get(),
            "outcome": outcome,
        }
        
        if error_class:
            event["error_class"] = error_class
        if duration_ms is not None:
            event["duration_ms"] = round(duration_ms, 2)
            
        event["details"] = scrub_secrets(details)
        
        # In a real app, this might go to a dedicated JSON log file or telemetry service.
        # For SVA, we emit it to the standard python logger at INFO, but as structured JSON.
        logger.info(json.dumps(event))

telemetry = TelemetryLogger()
