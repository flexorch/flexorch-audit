"""Integration tests for the public audit() and mask() API."""
import asyncio
import flexorch_audit
from flexorch_audit import audit, mask, audit_stream, compliance_report


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
    assert "[MASKED_EMAIL]" in clean


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


# ── New v0.5.0 fields: noise_ratio, detected_language, "und" locale ──────────

def test_audit_noise_ratio_field_present():
    result = audit("clean text\nmore text")
    assert "noise_ratio" in result
    assert isinstance(result["noise_ratio"], float)
    assert 0.0 <= result["noise_ratio"] <= 1.0


def test_audit_noise_ratio_attribute_access():
    result = audit("clean text")
    assert result.noise_ratio == result["noise_ratio"]


def test_audit_noise_ratio_noisy_text():
    noisy = "clean\n@@@symbol noise\n\nclean"
    result = audit(noisy)
    assert result.noise_ratio > 0.0


def test_audit_detected_language_field():
    result = audit("some text", locale="tr")
    assert result["detected_language"] == "tr"


def test_audit_detected_language_und_default():
    result = audit("some text")
    assert result["detected_language"] == "und"


def test_audit_locale_und_activates_all_detectors():
    text = "TC: 12345678950, SSN: 123-45-6789, email: x@y.com"
    result = audit(text, locale="und")
    types = {f["type"] for f in result["pii"]}
    assert "national_id_tr" in types
    assert "ssn" in types
    assert "email" in types


def test_audit_default_locale_is_und():
    text = "TC: 12345678950, SSN: 123-45-6789"
    result_und = audit(text, locale="und")
    result_default = audit(text)
    assert result_und["pii"] == result_default["pii"]


# ── audit_stream ──────────────────────────────────────────────────────────────


async def _collect(texts, locale="und"):
    results = []
    async def gen():
        for t in texts:
            yield t
    async for r in audit_stream(gen(), locale=locale):
        results.append(r)
    return results


def test_audit_stream_yields_results():
    texts = ["Hello world", "Contact: ali@example.com", "TCKN: 12345678950"]
    results = asyncio.run(_collect(texts, locale="tr"))
    assert len(results) == 3


def test_audit_stream_empty():
    results = asyncio.run(_collect([]))
    assert results == []


def test_audit_stream_result_has_grade():
    results = asyncio.run(_collect(["sample text"]))
    assert results[0].quality_grade in ("A", "B", "C", "D")


def test_audit_stream_detects_pii():
    results = asyncio.run(_collect(["Email: test@example.com"], locale="und"))
    assert any(f["type"] == "email" for f in results[0]["pii"])


# ── compliance_report ─────────────────────────────────────────────────────────


def test_compliance_no_pii():
    result = audit("The quick brown fox.", locale="tr")
    report = compliance_report(result)
    assert report["has_pii"] is False
    assert report["risk_level"] == "none"
    assert report["masking_required"] is False
    assert len(report["recommendations"]) == 1


def test_compliance_high_risk_tckn():
    result = audit("TC: 12345678950", locale="tr")
    report = compliance_report(result)
    assert report["has_pii"] is True
    assert report["risk_level"] == "high"
    assert report["masking_required"] is True
    assert "national_id_tr" in report["pii_types"]


def test_compliance_medium_risk_email():
    result = audit("Email: hello@example.com", locale="tr")
    report = compliance_report(result)
    assert report["risk_level"] == "medium"


def test_compliance_recommendations_present():
    result = audit("TC: 12345678950", locale="tr")
    report = compliance_report(result)
    assert isinstance(report["recommendations"], list)
    assert len(report["recommendations"]) >= 1


# ── redact_for_llm ────────────────────────────────────────────────────────────

def test_redact_for_llm_removes_pii():
    from flexorch_audit import redact_for_llm
    clean = redact_for_llm("TCKN: 12345678950, email: ali@example.com", locale="tr")
    assert "12345678950" not in clean
    assert "ali@example.com" not in clean


def test_redact_for_llm_no_pii_unchanged():
    from flexorch_audit import redact_for_llm
    text = "The quick brown fox jumps over the lazy dog."
    assert redact_for_llm(text) == text


def test_redact_for_llm_empty_string():
    from flexorch_audit import redact_for_llm
    assert redact_for_llm("") == ""


def test_redact_for_llm_strategy_token():
    from flexorch_audit import redact_for_llm
    clean = redact_for_llm("Email: hello@example.com", strategy="token")
    assert "hello@example.com" not in clean
    assert "<PII_EMAIL" in clean


def test_redact_for_llm_default_locale_und():
    from flexorch_audit import redact_for_llm
    # SSN detected with "und" (all detectors active)
    clean = redact_for_llm("SSN: 123-45-6789")
    assert "123-45-6789" not in clean


# ── estimate_tokens ───────────────────────────────────────────────────────────

def test_estimate_tokens_empty():
    from flexorch_audit import estimate_tokens
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0


def test_estimate_tokens_single_word():
    from flexorch_audit import estimate_tokens
    assert estimate_tokens("hello") >= 1


def test_estimate_tokens_scales_with_length():
    from flexorch_audit import estimate_tokens
    short = estimate_tokens("one two three")
    long = estimate_tokens("one two three " * 10)
    assert long > short


def test_estimate_tokens_rough_range():
    from flexorch_audit import estimate_tokens
    # "The quick brown fox" = 4 words → ~5-6 tokens expected
    result = estimate_tokens("The quick brown fox")
    assert 4 <= result <= 8


def test_estimate_tokens_returns_int():
    from flexorch_audit import estimate_tokens
    assert isinstance(estimate_tokens("some text"), int)


def test_compliance_pii_types_sorted():
    result = audit("TC: 12345678950 email: x@y.com", locale="tr")
    report = compliance_report(result)
    assert report["pii_types"] == sorted(report["pii_types"])
