"""Integration tests for the public audit() and mask() API."""
import flexorch_audit
from flexorch_audit import audit, mask


def test_version_present():
    assert isinstance(flexorch_audit.__version__, str)
    assert flexorch_audit.__version__.startswith("0.")


def test_audit_returns_all_pillars():
    result = audit("Hello world", locale="tr")
    assert "pii" in result
    assert "quality" in result
    assert "noise" in result


def test_audit_clean_text():
    result = audit("The quick brown fox jumps over the lazy dog.", locale="tr")
    assert result["pii"] == []
    assert result["quality"]["completeness"] == 1.0
    assert result["noise"]["garbage_ratio"] == 0.0


def test_audit_email_found():
    result = audit("Contact us: hello@flexorch.com", locale="tr")
    assert any(f["type"] == "email" for f in result["pii"])


def test_audit_tckn_found():
    result = audit("TC kimlik: 12345678950", locale="tr")
    assert any(f["type"] == "national_id_tr" for f in result["pii"])


def test_mask_redact_round_trip():
    text = "Email: test@example.com"
    result = audit(text, locale="tr")
    clean = mask(text, result["pii"], strategy="redact")
    assert "test@example.com" not in clean
    assert "[REDACTED_EMAIL]" in clean


def test_mask_no_pii_unchanged():
    text = "Clean text with no personal data."
    result = audit(text, locale="tr")
    assert mask(text, result["pii"]) == text


def test_audit_empty_string():
    result = audit("", locale="tr")
    assert result["pii"] == []
    assert result["quality"]["completeness"] == 0.0
    assert result["noise"]["encoding_ok"] is True


def test_audit_locale_us_ssn():
    result = audit("SSN: 123-45-6789", locale="us")
    assert any(f["type"] == "ssn" for f in result["pii"])


def test_audit_locale_all():
    text = "TC: 12345678950, SSN: 123-45-6789, email: x@y.com"
    result = audit(text, locale="all")
    types = {f["type"] for f in result["pii"]}
    assert "national_id_tr" in types
    assert "ssn" in types
    assert "email" in types


def test_mask_strategies_all_remove_pii():
    text = "Contact: ali@example.com"
    result = audit(text, locale="tr")
    for strategy in ("redact", "replace", "token", "hash"):
        clean = mask(text, result["pii"], strategy=strategy)
        assert "ali@example.com" not in clean, f"PII still present with strategy={strategy}"


# ── New fields: quality_grade, quality_score, pii_summary ────────────────────

def test_audit_quality_grade_present():
    result = audit("Hello world", locale="tr")
    assert result["quality_grade"] in ("A", "B", "C", "D")


def test_audit_quality_score_range():
    result = audit("Hello world", locale="tr")
    assert 0.0 <= result["quality_score"] <= 1.0


def test_audit_empty_text_grade_d():
    result = audit("")
    assert result["quality_grade"] == "D"
    assert result["quality_score"] == 0.0


def test_audit_long_clean_text_grade_a():
    result = audit("a" * 600)
    assert result["quality_grade"] == "A"
    assert result["quality_score"] >= 0.85


def test_audit_pii_summary_aggregates_by_type():
    result = audit("Email: a@b.com, c@d.com", locale="tr")
    assert isinstance(result["pii_summary"], list)
    email_entry = next((s for s in result["pii_summary"] if s["type"] == "email"), None)
    assert email_entry is not None
    assert email_entry["count"] == 2


def test_audit_pii_summary_empty_when_no_pii():
    result = audit("Clean text with no personal data.")
    assert result["pii_summary"] == []


def test_audit_result_attribute_access():
    result = audit("test text", locale="tr")
    assert result.quality_grade == result["quality_grade"]
    assert result.quality_score == result["quality_score"]
    assert result.pii == result["pii"]
    assert result.pii_summary == result["pii_summary"]
