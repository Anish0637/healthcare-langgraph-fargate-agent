from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PolicyDecision:
    allow: bool
    decision: str
    reason: str


ROLE_PERMISSIONS = {
    "clinician": {"treatment", "care_coordination"},
    "billing": {"payment", "operations"},
    "researcher": {"research_deidentified"},
}


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def authorize(
    role: str,
    tenant_id: str,
    purpose_of_use: str,
    attributes: dict,
    context: dict,
    patient_context: dict,
) -> PolicyDecision:
    # RBAC
    allowed_purposes = ROLE_PERMISSIONS.get(role, set())
    if purpose_of_use not in allowed_purposes:
        return PolicyDecision(False, "deny", "rbac_purpose_not_allowed")

    # ABAC
    if attributes.get("tenant_id") and attributes.get("tenant_id") != tenant_id:
        return PolicyDecision(False, "deny", "abac_tenant_mismatch")
    if attributes.get("env") == "prod" and attributes.get("data_class") == "restricted" and role != "clinician":
        return PolicyDecision(False, "deny", "abac_restricted_data")

    # CBAC
    request_time = _parse_time(context.get("request_time_utc"))
    if role == "billing" and request_time.hour < 6:
        return PolicyDecision(False, "deny", "cbac_off_hours")

    break_glass = context.get("break_glass", False)
    consent = bool(patient_context.get("consent", False))
    if purpose_of_use == "treatment" and not consent and not break_glass:
        return PolicyDecision(False, "deny", "cbac_missing_consent")

    return PolicyDecision(True, "allow", "ok")
