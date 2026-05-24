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


# ── replace strategy — valid synthetic values ─────────────────────────────────

from flexorch_audit._pii import _valid_tckn, _valid_iban


def test_replace_tckn_is_valid():
    findings = [{"type": "national_id_tr", "value": "12345678950", "start": 4, "end": 15}]
    result = apply_mask("ID: 12345678950 end", findings, strategy="replace")
    replaced = result[4:15]
    assert _valid_tckn(replaced) is True


def test_replace_tckn_is_deterministic():
    findings = [{"type": "national_id_tr", "value": "12345678950", "start": 0, "end": 11}]
    r1 = apply_mask("12345678950", findings, strategy="replace")
    r2 = apply_mask("12345678950", findings, strategy="replace")
    assert r1 == r2


def test_replace_iban_tr_is_valid():
    findings = [{"type": "iban_tr", "value": "TR330006100519786457841326", "start": 6, "end": 32}]
    result = apply_mask("IBAN: TR330006100519786457841326 ok", findings, strategy="replace")
    replaced = result[6:32]
    assert replaced.startswith("TR")
    assert _valid_iban(replaced.replace(" ", "")) is True


def test_replace_name_from_pool():
    findings = [{"type": "name", "value": "Ali Yıldız", "start": 5, "end": 15}]
    result = apply_mask("Ad: Ali Yıldız ok", findings, strategy="replace")
    assert "Ali Yıldız" not in result
    assert len(result.split()[1]) > 0  # replaced with something


def test_replace_unknown_type_uses_tag():
    findings = [{"type": "unknown_type_x", "value": "abc", "start": 0, "end": 3}]
    result = apply_mask("abc", findings, strategy="replace")
    assert result == "[UNKNOWN_TYPE_X]"
