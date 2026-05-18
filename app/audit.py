import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.pii import redact_text


logger = logging.getLogger("audit")
logging.basicConfig(level=logging.INFO)


def _sanitize_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_obj(i) for i in obj]
    return obj


def audit_event(event_type: str, trace_id: str, payload: dict[str, Any]) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "trace_id": trace_id,
        "payload": _sanitize_obj(payload),
    }
    logger.info(json.dumps(record, separators=(",", ":")))
