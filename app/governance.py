from app.pii import redact_text


TOOL_POLICY = {
    "get_utc_time": {"min_role": "researcher", "requires_phi": False},
    "patient_risk_score": {"min_role": "clinician", "requires_phi": True},
}

ROLE_ORDER = {"researcher": 1, "billing": 1, "clinician": 2}

BLOCK_PATTERNS = [
    "ignore previous instructions",
    "exfiltrate",
    "dump all patient",
]


def check_guardrails(message: str) -> tuple[bool, str]:
    lowered = message.lower()
    for pattern in BLOCK_PATTERNS:
        if pattern in lowered:
            return False, "guardrail_prompt_injection"
    return True, "ok"


def enforce_tool_governance(tool_name: str, role: str, has_phi_context: bool) -> tuple[bool, str]:
    rule = TOOL_POLICY.get(tool_name)
    if not rule:
        return False, "tool_not_registered"
    if ROLE_ORDER.get(role, 0) < ROLE_ORDER.get(rule["min_role"], 99):
        return False, "tool_role_forbidden"
    if rule["requires_phi"] and not has_phi_context:
        return False, "tool_phi_context_required"
    return True, "ok"


def sanitize_for_model(message: str) -> str:
    return redact_text(message)


def sanitize_for_output(text: str) -> str:
    return redact_text(text)
