from app.pii import redact_text


def test_redact_basic_pii():
    text = "Email a@b.com, SSN 123-45-6789, MRN: X123"
    out = redact_text(text)
    assert "[REDACTED]" in out
