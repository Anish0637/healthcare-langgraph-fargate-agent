import re

PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
]

PHI_HINT_PATTERNS = [
    re.compile(r"\bMRN[: ]*\w+\b", re.IGNORECASE),
    re.compile(r"\bDOB[: ]*\d{1,2}/\d{1,2}/\d{2,4}\b", re.IGNORECASE),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in PII_PATTERNS + PHI_HINT_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
