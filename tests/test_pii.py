import pytest
from flexorch_audit._pii import (
    detect_pii, _valid_tckn, _luhn, _valid_vkn, _valid_iban,
    _valid_iban_intl, _valid_phone_intl,
    _valid_steuer_id_de, _valid_partita_iva_it, _valid_bsn_nl,
    _valid_dni_es, _valid_nie_es, _valid_ni_uk, _valid_ein_us,
)


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
    # locale="tr" → iban_tr type (replaces generic iban for TR locale)
    findings = detect_pii("IBAN: TR330006100519786457841326", locale="tr")
    assert any(f["type"] == "iban_tr" for f in findings)


def test_iban_tr_not_generic_iban():
    # generic iban must not fire alongside iban_tr
    findings = detect_pii("IBAN: TR330006100519786457841326", locale="tr")
    assert not any(f["type"] == "iban" for f in findings)


def test_iban_de_detected_tr_locale():
    # German IBAN in TR locale: no iban_intl active → falls back to universal iban
    findings = detect_pii("Bank: DE89370400440532013000", locale="tr")
    assert any(f["type"] == "iban" for f in findings)


def test_iban_de_detected_eu_locale():
    # locale="eu" → iban_intl with country/length validation
    findings = detect_pii("Bank: DE89370400440532013000", locale="eu")
    assert any(f["type"] == "iban_intl" for f in findings)


def test_iban_intl_no_generic_iban_eu():
    # generic iban must not fire alongside iban_intl
    findings = detect_pii("Bank: DE89370400440532013000", locale="eu")
    assert not any(f["type"] == "iban" for f in findings)


def test_iban_invalid_checksum_rejected():
    findings = detect_pii("DE00370400440532013000", locale="eu")
    assert not any(f["type"] == "iban_intl" for f in findings)


def test_iban_unsupported_country_rejected():
    findings = detect_pii("JP00XXXX0000000000000000", locale="eu")
    assert not any(f["type"] == "iban_intl" for f in findings)


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


# ── VKN ───────────────────────────────────────────────────────────────────────


def test_valid_vkn():
    assert _valid_vkn("1234567890") is True
    assert _valid_vkn("9876543217") is True


def test_invalid_vkn_checksum():
    assert _valid_vkn("1234567891") is False


def test_invalid_vkn_leading_zero():
    assert _valid_vkn("0123456789") is False


def test_invalid_vkn_non_numeric():
    assert _valid_vkn("123456789X") is False


def test_vkn_detected_tr_locale():
    findings = detect_pii("VKN: 1234567890", locale="tr")
    assert any(f["type"] == "tax_id_tr" and f["value"] == "1234567890" for f in findings)


def test_invalid_vkn_not_detected():
    findings = detect_pii("VKN: 1234567891", locale="tr")
    assert not any(f["type"] == "tax_id_tr" for f in findings)


def test_vkn_not_detected_us_locale():
    findings = detect_pii("VKN: 1234567890", locale="us")
    assert not any(f["type"] == "tax_id_tr" for f in findings)


def test_tckn_not_matched_as_vkn():
    # 11-digit TCKN must not trigger 10-digit VKN match
    findings = detect_pii("TC: 12345678950", locale="tr")
    assert not any(f["type"] == "tax_id_tr" for f in findings)


# ── IPv6 ──────────────────────────────────────────────────────────────────────


def test_ipv6_full_detected():
    findings = detect_pii("Server: 2001:0db8:85a3:0000:0000:8a2e:0370:7334", locale="tr")
    assert any(f["type"] == "ip_v6" for f in findings)


def test_ipv6_compressed_detected():
    findings = detect_pii("Host: 2001:db8::1", locale="tr")
    assert any(f["type"] == "ip_v6" and "2001:db8::1" in f["value"] for f in findings)


def test_ipv6_loopback_detected():
    findings = detect_pii("Loopback: ::1", locale="tr")
    assert any(f["type"] == "ip_v6" for f in findings)


def test_ipv6_not_detected_in_clean_text():
    findings = detect_pii("Version 1:2 is available", locale="tr")
    assert not any(f["type"] == "ip_v6" for f in findings)


# ── IBAN mod-97 ───────────────────────────────────────────────────────────────


def test_valid_iban_de():
    assert _valid_iban("DE89370400440532013000") is True


def test_valid_iban_tr():
    assert _valid_iban("TR330006100519786457841326") is True


def test_invalid_iban_checksum():
    # Flip one digit — fails mod-97
    assert _valid_iban("DE89370400440532013001") is False


def test_invalid_iban_not_detected():
    # Format matches regex but fails mod-97
    findings = detect_pii("IBAN: DE89370400440532013001", locale="tr")
    assert not any(f["type"] == "iban" for f in findings)


# ── audit_batch ───────────────────────────────────────────────────────────────


def test_audit_batch_empty():
    from flexorch_audit import audit_batch
    result = audit_batch([])
    assert result["duplicate_ratio"] == 0.0
    assert result["results"] == []


def test_audit_batch_no_duplicates():
    from flexorch_audit import audit_batch
    texts = ["Hello world", "Different text", "Another one"]
    result = audit_batch(texts)
    assert result["duplicate_ratio"] == 0.0
    assert len(result["results"]) == 3


def test_audit_batch_with_duplicates():
    from flexorch_audit import audit_batch
    texts = ["Same text", "Same text", "Different"]
    result = audit_batch(texts)
    assert result["duplicate_ratio"] == pytest.approx(1 / 3, abs=0.001)


def test_audit_batch_all_duplicates():
    from flexorch_audit import audit_batch
    texts = ["copy", "copy", "copy"]
    result = audit_batch(texts)
    assert result["duplicate_ratio"] == pytest.approx(2 / 3, abs=0.001)


def test_audit_batch_pii_summary_aggregated():
    from flexorch_audit import audit_batch
    texts = [
        "Email: a@b.com",
        "Email: c@d.com and e@f.com",
    ]
    result = audit_batch(texts, locale="tr")
    email_entry = next((x for x in result["pii_summary"] if x["type"] == "email"), None)
    assert email_entry is not None
    assert email_entry["count"] == 3


def test_audit_batch_avg_quality_score():
    from flexorch_audit import audit_batch
    texts = ["", "Hello world " * 100]
    result = audit_batch(texts)
    assert 0.0 < result["avg_quality_score"] < 1.0


# ── phone_intl ────────────────────────────────────────────────────────────────


def test_phone_intl_us_detected():
    findings = detect_pii("Call: +1 (415) 555-2671", locale="us")
    assert any(f["type"] == "phone_intl" and f["value"].startswith("+1") for f in findings)


def test_phone_intl_uk_detected():
    findings = detect_pii("Tel: +44 20 7946 0958", locale="eu")
    assert any(f["type"] == "phone_intl" and f["value"].startswith("+44") for f in findings)


def test_phone_intl_tr_excluded():
    # +90 TR numbers must not appear as phone_intl in any locale
    findings = detect_pii("+905321234567", locale="eu")
    assert not any(f["type"] == "phone_intl" for f in findings)


def test_phone_intl_too_short_rejected():
    assert not any(f["type"] == "phone_intl" for f in detect_pii("+123456", locale="eu"))


def test_phone_intl_not_in_tr_locale():
    findings = detect_pii("Tel: +44 20 7946 0958", locale="tr")
    assert not any(f["type"] == "phone_intl" for f in findings)


def test_valid_phone_intl_helper():
    assert _valid_phone_intl("+14155552671") is True
    assert _valid_phone_intl("+905321234567") is False  # TR excluded
    assert _valid_phone_intl("+123456") is False          # too short


# ── company_name_tr ───────────────────────────────────────────────────────────


def test_company_name_tr_as_detected():
    findings = detect_pii("Tedarikçi: Arçelik A.Ş. fatura kesti.", locale="tr")
    assert any(f["type"] == "company_name_tr" and "Arçelik" in f["value"] for f in findings)


def test_company_name_tr_ltd_sti():
    findings = detect_pii("Firma: Delta Yazılım Ltd. Şti. ile anlaşıldı.", locale="tr")
    assert any(f["type"] == "company_name_tr" for f in findings)


def test_company_name_tr_not_in_eu_locale():
    findings = detect_pii("Firma: Arçelik A.Ş.", locale="eu")
    assert not any(f["type"] == "company_name_tr" for f in findings)


# ── mersis_no ─────────────────────────────────────────────────────────────────


def test_mersis_detected():
    findings = detect_pii("MERSİS: 1234567890123456", locale="tr")
    assert any(f["type"] == "mersis_no" and f["value"] == "1234567890123456" for f in findings)


def test_mersis_starts_with_zero_not_detected():
    findings = detect_pii("0234567890123456", locale="tr")
    assert not any(f["type"] == "mersis_no" for f in findings)


def test_mersis_not_in_us_locale():
    findings = detect_pii("MERSİS: 1234567890123456", locale="us")
    assert not any(f["type"] == "mersis_no" for f in findings)


# ── postal_code_tr ────────────────────────────────────────────────────────────


def test_postal_code_tr_detected():
    findings = detect_pii("Posta kodu: 34100 İstanbul", locale="tr")
    assert any(f["type"] == "postal_code_tr" and f["value"] == "34100" for f in findings)


def test_postal_code_tr_invalid_province_rejected():
    # 99xxx — province plate 99 doesn't exist
    findings = detect_pii("Kod: 99100", locale="tr")
    assert not any(f["type"] == "postal_code_tr" for f in findings)


# ── province_tr ───────────────────────────────────────────────────────────────


def test_province_tr_detected():
    findings = detect_pii("Şehir: İstanbul", locale="tr")
    assert any(f["type"] == "province_tr" and f["value"] == "İstanbul" for f in findings)


def test_province_tr_ankara():
    findings = detect_pii("Ankara'da bir toplantı yapıldı.", locale="tr")
    assert any(f["type"] == "province_tr" and f["value"] == "Ankara" for f in findings)


def test_province_tr_not_in_eu_locale():
    findings = detect_pii("City: İstanbul", locale="eu")
    assert not any(f["type"] == "province_tr" for f in findings)


# ── company_name_intl ─────────────────────────────────────────────────────────


def test_company_name_intl_gmbh():
    findings = detect_pii("Tedarikçi: Müller Elektronik GmbH fatura kesti.", locale="eu")
    assert any(f["type"] == "company_name_intl" and "GmbH" in f["value"] for f in findings)


def test_company_name_intl_llc():
    findings = detect_pii("Vendor: Acme Solutions LLC", locale="us")
    assert any(f["type"] == "company_name_intl" and "LLC" in f["value"] for f in findings)


def test_company_name_intl_sas():
    findings = detect_pii("Alıcı: Renault SAS sözleşmeyi imzaladı.", locale="eu")
    assert any(f["type"] == "company_name_intl" and "SAS" in f["value"] for f in findings)


def test_company_name_intl_lowercase_start_rejected():
    findings = detect_pii("bu bir gmbh değildir.", locale="eu")
    assert not any(f["type"] == "company_name_intl" for f in findings)


def test_company_name_intl_not_in_tr_locale():
    findings = detect_pii("Firma: Bosch GmbH ile anlaşma.", locale="tr")
    assert not any(f["type"] == "company_name_intl" for f in findings)


# ── iban_intl validators ──────────────────────────────────────────────────────


def test_valid_iban_intl_de():
    assert _valid_iban_intl("DE89370400440532013000") is True


def test_valid_iban_intl_nl():
    assert _valid_iban_intl("NL91ABNA0417164300") is True


def test_valid_iban_intl_tr_excluded():
    assert _valid_iban_intl("TR330006100519786457841326") is False


def test_valid_iban_intl_wrong_length():
    # DE should be 22 chars; 21 chars → rejected
    assert _valid_iban_intl("DE89370400440532013") is False


def test_valid_iban_intl_bad_checksum():
    assert _valid_iban_intl("DE00370400440532013000") is False


# ── locale="all" combined ─────────────────────────────────────────────────────


def test_locale_all_tr_iban_as_iban_tr():
    findings = detect_pii("TR330006100519786457841326", locale="all")
    assert any(f["type"] == "iban_tr" for f in findings)
    assert not any(f["type"] == "iban" for f in findings)


def test_locale_all_de_iban_as_iban_intl():
    findings = detect_pii("DE89370400440532013000", locale="all")
    assert any(f["type"] == "iban_intl" for f in findings)
    assert not any(f["type"] == "iban" for f in findings)



# ── S2.1 DE ───────────────────────────────────────────────────────────────────

def test_steuer_id_de_valid():
    assert _valid_steuer_id_de("47036892816") is True


def test_steuer_id_de_invalid_checksum():
    assert _valid_steuer_id_de("47036892815") is False


def test_steuer_id_de_leading_zero_rejected():
    assert _valid_steuer_id_de("04703689281") is False


def test_tax_id_de_detected():
    findings = detect_pii("IdNr 47036892816", locale="de")
    assert any(f["type"] == "tax_id_de" and f["value"] == "47036892816" for f in findings)


def test_tax_id_de_not_in_tr_locale():
    findings = detect_pii("47036892816", locale="tr")
    assert not any(f["type"] == "tax_id_de" for f in findings)


def test_social_id_de_detected():
    findings = detect_pii("SV-Nr 12800101A0001", locale="de")
    assert any(f["type"] == "social_id_de" and f["value"] == "12800101A0001" for f in findings)


# ── S2.2 FR ───────────────────────────────────────────────────────────────────


def test_siret_fr_detected():
    findings = detect_pii("SIRET: 12345678901234", locale="fr")
    assert any(f["type"] == "siret_fr" and f["value"] == "12345678901234" for f in findings)


def test_siren_fr_detected():
    findings = detect_pii("SIREN: 123456789", locale="fr")
    assert any(f["type"] == "company_id_fr" and f["value"] == "123456789" for f in findings)


def test_insee_fr_detected():
    findings = detect_pii("NIR: 195127512345678", locale="fr")
    assert any(f["type"] == "social_id_fr" and f["value"] == "195127512345678" for f in findings)


def test_insee_fr_starts_with_3_not_detected():
    findings = detect_pii("395127512345678", locale="fr")
    assert not any(f["type"] == "social_id_fr" for f in findings)


# ── S2.3 IT ───────────────────────────────────────────────────────────────────


def test_partita_iva_valid():
    assert _valid_partita_iva_it("12345678903") is True


def test_partita_iva_wrong_checksum():
    assert _valid_partita_iva_it("12345678900") is False


def test_codice_fiscale_detected():
    findings = detect_pii("CF: RSSMRA85M01H501Z", locale="it")
    assert any(f["type"] == "national_id_it" and f["value"] == "RSSMRA85M01H501Z" for f in findings)


def test_partita_iva_detected():
    findings = detect_pii("P.IVA 12345678903", locale="it")
    assert any(f["type"] == "tax_id_it" and f["value"] == "12345678903" for f in findings)


# ── S2.4 NL ───────────────────────────────────────────────────────────────────


def test_bsn_nl_valid():
    assert _valid_bsn_nl("123456782") is True


def test_bsn_nl_invalid():
    assert _valid_bsn_nl("123456780") is False


def test_bsn_nl_detected():
    findings = detect_pii("BSN: 123456782", locale="nl")
    assert any(f["type"] == "national_id_nl" and f["value"] == "123456782" for f in findings)


def test_kvk_nl_detected():
    findings = detect_pii("KvK: 12345678", locale="nl")
    assert any(f["type"] == "company_id_nl" and f["value"] == "12345678" for f in findings)


# ── S2.5 ES ───────────────────────────────────────────────────────────────────


def test_dni_es_valid():
    assert _valid_dni_es("12345678Z") is True


def test_dni_es_invalid_letter():
    assert _valid_dni_es("12345678A") is False


def test_nie_es_valid():
    assert _valid_nie_es("X1234567L") is True


def test_dni_detected():
    findings = detect_pii("DNI: 12345678Z", locale="es")
    assert any(f["type"] == "national_id_es" and f["value"] == "12345678Z" for f in findings)


def test_cif_detected():
    findings = detect_pii("CIF: B12345674", locale="es")
    assert any(f["type"] == "tax_id_es" and f["value"] == "B12345674" for f in findings)


# ── S2.6 UK ───────────────────────────────────────────────────────────────────


def test_ni_uk_valid():
    assert _valid_ni_uk("AB123456A") is True


def test_ni_uk_forbidden():
    assert _valid_ni_uk("BG123456A") is False


def test_ni_uk_detected():
    findings = detect_pii("NI: AB123456A", locale="uk")
    assert any(f["type"] == "social_id_uk" and f["value"] == "AB123456A" for f in findings)


def test_utr_detected():
    findings = detect_pii("UTR: 1234567890", locale="uk")
    assert any(f["type"] == "tax_id_uk" and f["value"] == "1234567890" for f in findings)


# ── S2.7 US ───────────────────────────────────────────────────────────────────


def test_ein_us_valid():
    assert _valid_ein_us("12-3456789") is True


def test_ein_us_invalid_prefix():
    assert _valid_ein_us("00-1234567") is False


def test_ein_detected():
    findings = detect_pii("EIN: 12-3456789", locale="us")
    assert any(f["type"] == "tax_id_us" and f["value"] == "12-3456789" for f in findings)


def test_itin_detected():
    findings = detect_pii("ITIN: 900-70-1234", locale="us")
    assert any(f["type"] == "national_id_us" and f["value"] == "900-70-1234" for f in findings)


def test_ssn_still_detected_in_us_locale():
    findings = detect_pii("SSN: 555-12-1234", locale="us")
    assert any(f["type"] == "ssn" for f in findings)


# -- PL -- PESEL --------------------------------------------------------------

from flexorch_audit._pii import _valid_pesel_pl, _valid_svnr_at, _valid_nrrniss_be


def test_valid_pesel_pl():
    # 44051401359 -- born 1944-05-14, check digit 9 (total=101, (10-1)%10=9)
    assert _valid_pesel_pl("44051401359") is True


def test_invalid_pesel_wrong_checksum():
    assert _valid_pesel_pl("44051401358") is False


def test_pesel_detected_pl_locale():
    findings = detect_pii("PESEL: 44051401359", locale="pl")
    assert any(f["type"] == "national_id_pl" and f["value"] == "44051401359" for f in findings)


def test_pesel_not_detected_tr_locale():
    findings = detect_pii("PESEL: 44051401359", locale="tr")
    assert not any(f["type"] == "national_id_pl" for f in findings)


def test_pesel_detected_und_locale():
    findings = detect_pii("PESEL: 44051401359", locale="und")
    assert any(f["type"] == "national_id_pl" for f in findings)


def test_invalid_pesel_length():
    assert _valid_pesel_pl("4405140135") is False
    assert _valid_pesel_pl("440514013590") is False


# -- AT -- SVNr ---------------------------------------------------------------


def test_valid_svnr_at():
    # 1232010180: total=3*1+7*2+9*3+5*0+8*1+4*0+2*1+1*8+6*0=62, 62%10=2 -> pos3=2
    assert _valid_svnr_at("1232010180") is True


def test_invalid_svnr_at():
    assert _valid_svnr_at("1234010180") is False


def test_svnr_detected_at_locale():
    findings = detect_pii("SVNr: 1232010180", locale="at")
    assert any(f["type"] == "social_id_at" and f["value"] == "1232010180" for f in findings)


def test_svnr_not_detected_tr_locale():
    findings = detect_pii("SVNr: 1232010180", locale="tr")
    assert not any(f["type"] == "social_id_at" for f in findings)


def test_svnr_detected_und_locale():
    findings = detect_pii("SVNr: 1232010180", locale="und")
    assert any(f["type"] == "social_id_at" for f in findings)


# -- BE -- Rijksregisternummer ------------------------------------------------


def test_valid_nrrniss_be_pre2000():
    body = 930101001
    check = 97 - (body % 97)
    s = f"{body:09d}{check:02d}"
    assert _valid_nrrniss_be(s) is True


def test_valid_nrrniss_be_post2000():
    body = 20314002
    body2k = 2_000_000_000 + body
    check = 97 - (body2k % 97)
    s = f"{body:09d}{check:02d}"
    assert _valid_nrrniss_be(s) is True


def test_invalid_nrrniss_be():
    assert _valid_nrrniss_be("93010100100") is False


def test_nrrniss_detected_be_locale():
    body = 930101001
    check = 97 - (body % 97)
    s = f"{body:09d}{check:02d}"
    findings = detect_pii(f"RRN: {s}", locale="be")
    assert any(f["type"] == "national_id_be" and f["value"] == s for f in findings)


def test_nrrniss_not_detected_tr_locale():
    body = 930101001
    check = 97 - (body % 97)
    s = f"{body:09d}{check:02d}"
    findings = detect_pii(f"RRN: {s}", locale="tr")
    assert not any(f["type"] == "national_id_be" for f in findings)


def test_nrrniss_detected_und_locale():
    body = 930101001
    check = 97 - (body % 97)
    s = f"{body:09d}{check:02d}"
    findings = detect_pii(f"RRN: {s}", locale="und")
    assert any(f["type"] == "national_id_be" for f in findings)
