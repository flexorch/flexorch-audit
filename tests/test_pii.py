import pytest
from flexorch_audit._pii import detect_pii, _valid_tckn, _luhn


# ── TCKN checksum ─────────────────────────────────────────────────────────────


def test_valid_tckn():
    # Computed: d=[1,2,3,4,5,6,7,8,9,5,0], sum_odd=25, sum_even=20
    # d9=(175-20)%10=5, d10=50%10=0
    assert _valid_tckn("12345678950") is True


def test_invalid_tckn_wrong_checksum():
    assert _valid_tckn("12345678900") is False


def test_invalid_tckn_starts_with_zero():
    assert _valid_tckn("01234567890") is False


def test_invalid_tckn_wrong_length():
    assert _valid_tckn("1234567890") is False


# ── Luhn ─────────────────────────────────────────────────────────────────────


def test_luhn_valid_visa():
    assert _luhn("4532015112830366") is True


def test_luhn_invalid():
    assert _luhn("1234567890123456") is False


def test_luhn_too_short():
    assert _luhn("123456") is False


# ── Email ─────────────────────────────────────────────────────────────────────


def test_email_detected():
    findings = detect_pii("Contact: test@example.com today", locale="tr")
    assert any(f["type"] == "email" and f["value"] == "test@example.com" for f in findings)


def test_email_subdomain():
    findings = detect_pii("Send to ali@mail.co.uk", locale="tr")
    assert any(f["type"] == "email" for f in findings)


def test_no_email_in_clean_text():
    findings = detect_pii("Hello world, no PII here.", locale="tr")
    assert not any(f["type"] == "email" for f in findings)


# ── Turkish phone ─────────────────────────────────────────────────────────────


def test_phone_tr_with_prefix():
    findings = detect_pii("Ara: +90 532 123 45 67", locale="tr")
    assert any(f["type"] == "phone_tr" for f in findings)


def test_phone_tr_domestic():
    findings = detect_pii("GSM: 0532 123 45 67", locale="tr")
    assert any(f["type"] == "phone_tr" for f in findings)


def test_phone_tr_not_in_us_locale():
    findings = detect_pii("GSM: 0532 123 45 67", locale="us")
    assert not any(f["type"] == "phone_tr" for f in findings)


# ── TCKN ──────────────────────────────────────────────────────────────────────


def test_tckn_detected():
    findings = detect_pii("TC: 12345678950", locale="tr")
    assert any(f["type"] == "national_id_tr" and f["value"] == "12345678950" for f in findings)


def test_invalid_tckn_not_detected():
    findings = detect_pii("TC: 12345678900", locale="tr")
    assert not any(f["type"] == "national_id_tr" for f in findings)


def test_tckn_not_in_us_locale():
    findings = detect_pii("TC: 12345678950", locale="us")
    assert not any(f["type"] == "national_id_tr" for f in findings)


# ── IBAN ──────────────────────────────────────────────────────────────────────


def test_iban_tr_detected():
    findings = detect_pii("IBAN: TR330006100519786457841326", locale="tr")
    assert any(f["type"] == "iban" for f in findings)


def test_iban_de_detected():
    findings = detect_pii("Bank: DE89370400440532013000", locale="tr")
    assert any(f["type"] == "iban" for f in findings)


# ── Credit card ───────────────────────────────────────────────────────────────


def test_credit_card_detected():
    # Known Luhn-valid Visa test number
    findings = detect_pii("Card: 4532 0151 1283 0366", locale="tr")
    assert any(f["type"] == "credit_card" for f in findings)


def test_invalid_cc_not_detected():
    findings = detect_pii("Ref: 1234 5678 9012 3456", locale="tr")
    assert not any(f["type"] == "credit_card" for f in findings)


# ── IP ────────────────────────────────────────────────────────────────────────


def test_ip_detected():
    findings = detect_pii("Server: 192.168.1.100", locale="tr")
    assert any(f["type"] == "ip" and f["value"] == "192.168.1.100" for f in findings)


def test_invalid_ip_not_detected():
    findings = detect_pii("Bad IP: 999.999.999.999", locale="tr")
    assert not any(f["type"] == "ip" for f in findings)


# ── SSN ───────────────────────────────────────────────────────────────────────


def test_ssn_detected_us_locale():
    findings = detect_pii("SSN: 123-45-6789", locale="us")
    assert any(f["type"] == "ssn" and f["value"] == "123-45-6789" for f in findings)


def test_ssn_not_detected_tr_locale():
    findings = detect_pii("SSN: 123-45-6789", locale="tr")
    assert not any(f["type"] == "ssn" for f in findings)


def test_ssn_invalid_000_not_detected():
    findings = detect_pii("SSN: 000-45-6789", locale="us")
    assert not any(f["type"] == "ssn" for f in findings)


# ── Name ──────────────────────────────────────────────────────────────────────


def test_name_tr_label():
    findings = detect_pii("Adı Soyadı: Ahmet Yıldız", locale="tr")
    assert any(f["type"] == "name" and "Ahmet" in f["value"] for f in findings)


def test_name_en_label():
    findings = detect_pii("Full Name: John Smith", locale="tr")
    assert any(f["type"] == "name" and "John" in f["value"] for f in findings)


def test_name_not_detected_us_locale():
    findings = detect_pii("Adı: Ahmet Yıldız", locale="us")
    assert not any(f["type"] == "name" for f in findings)


# ── Locale: all ───────────────────────────────────────────────────────────────


def test_locale_all_includes_tckn_and_ssn():
    text = "TC: 12345678950 and SSN: 123-45-6789"
    findings = detect_pii(text, locale="all")
    types = {f["type"] for f in findings}
    assert "national_id_tr" in types
    assert "ssn" in types


def test_findings_sorted_by_position():
    text = "Email: a@b.com phone: 0532 123 45 67"
    findings = detect_pii(text, locale="tr")
    starts = [f["start"] for f in findings]
    assert starts == sorted(starts)


def test_empty_string_returns_empty():
    assert detect_pii("", locale="tr") == []
    assert detect_pii("   ", locale="tr") == []
