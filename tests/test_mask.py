import pytest
from flexorch_audit._mask import apply_mask


_FINDINGS = [{"type": "email", "value": "a@b.com", "start": 7, "end": 14}]
_TEXT = "Email: a@b.com end"


def test_redact_strategy():
    result = apply_mask(_TEXT, _FINDINGS, strategy="redact")
    assert "a@b.com" not in result
    assert "[REDACTED_EMAIL]" in result


def test_replace_strategy():
    result = apply_mask(_TEXT, _FINDINGS, strategy="replace")
    assert "a@b.com" not in result
    assert "example.com" in result


def test_token_strategy():
    result = apply_mask(_TEXT, _FINDINGS, strategy="token")
    assert "a@b.com" not in result
    assert "<PII_EMAIL_1>" in result


def test_hash_strategy():
    result = apply_mask(_TEXT, _FINDINGS, strategy="hash")
    assert "a@b.com" not in result
    # Hash replacement is 16 hex chars wrapped in []
    import re
    assert re.search(r"\[[0-9a-f]{16}\]", result)


def test_default_strategy_is_redact():
    result = apply_mask(_TEXT, _FINDINGS)
    assert "[REDACTED_EMAIL]" in result


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown strategy"):
        apply_mask(_TEXT, _FINDINGS, strategy="invalid")


def test_empty_findings_returns_original():
    assert apply_mask(_TEXT, []) == _TEXT


def test_empty_text_returns_empty():
    assert apply_mask("", _FINDINGS) == ""


def test_multiple_findings_correct_order():
    text = "a@b.com and c@d.com"
    findings = [
        {"type": "email", "value": "a@b.com", "start": 0, "end": 7},
        {"type": "email", "value": "c@d.com", "start": 12, "end": 19},
    ]
    result = apply_mask(text, findings, strategy="redact")
    assert "a@b.com" not in result
    assert "c@d.com" not in result
    assert result.count("[REDACTED_EMAIL]") == 2


def test_token_counter_per_type():
    text = "a@b.com c@d.com"
    findings = [
        {"type": "email", "value": "a@b.com", "start": 0, "end": 7},
        {"type": "email", "value": "c@d.com", "start": 8, "end": 15},
    ]
    result = apply_mask(text, findings, strategy="token")
    # Tokens count up per type
    assert "<PII_EMAIL_" in result


def test_phone_tr_replace_synthetic():
    text = "Tel: 0532 123 45 67"
    findings = [{"type": "phone_tr", "value": "0532 123 45 67", "start": 5, "end": 19}]
    result = apply_mask(text, findings, strategy="replace")
    assert "0532 123 45 67" not in result
    assert "0500 000 00 00" in result


def test_hash_is_deterministic():
    r1 = apply_mask(_TEXT, _FINDINGS, strategy="hash")
    r2 = apply_mask(_TEXT, _FINDINGS, strategy="hash")
    assert r1 == r2
