import re

# ── Universal detectors ──────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# E.164 international phone — requires + prefix, 7-15 total digits, TR (+90) excluded.
# Validated by _valid_phone_intl(); type: "phone_intl" in eu/us locales.
PHONE_INTL_RE = re.compile(r"(?<![+\d])(\+[1-9][\d\s\-\.\(\)]{5,18}\d)(?!\d)")

# IBAN — ISO 13616 generic; mod-97 validated by _valid_iban().
# Locale-specific sub-types (iban_tr, iban_intl) replace this in tr/eu locales.
IBAN_RE = re.compile(r"\b([A-Z]{2}\d{2}[0-9A-Z]{11,30})\b")

# Credit card — 16 digits with separator groups (Luhn-validated)
CC_RE = re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")

# IPv4
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 — full, compressed (::), and loopback forms
_H = r"[0-9a-fA-F]{1,4}"
IPV6_RE = re.compile(
    rf"(?<![:\.\w])"
    rf"(?:"
    rf"(?:{_H}:){{7}}{_H}"
    rf"|(?:{_H}:){{1,7}}:"
    rf"|::(?:(?:{_H}:){{0,6}}{_H})?"
    rf"|(?:{_H}:){{1,6}}:{_H}"
    rf"|(?:{_H}:){{1,5}}(?::{_H}){{1,2}}"
    rf"|(?:{_H}:){{1,4}}(?::{_H}){{1,3}}"
    rf"|(?:{_H}:){{1,3}}(?::{_H}){{1,4}}"
    rf"|(?:{_H}:){{1,2}}(?::{_H}){{1,5}}"
    rf"|{_H}:(?::{_H}){{1,6}}"
    rf")"
    rf"(?![:\.\w])",
    re.IGNORECASE,
)

# ── Turkish detectors ────────────────────────────────────────────────────────

# Turkish mobile: +90 5xx... or 0 5xx... or bare 5xx (10 digits)
PHONE_TR_RE = re.compile(r"\b(?:\+90|0)?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}\b")

# TCKN — first digit non-zero, 11 digits, checksum-validated
TCKN_RE = re.compile(r"\b([1-9]\d{10})\b")

# VKN (Vergi Kimlik Numarası) — 10 digits, first non-zero, Luhn-variant checksum
VKN_RE = re.compile(r"\b([1-9]\d{9})\b")

# Turkish IBAN — TR + 2 check + 22 BBAN digits/chars (total 26)
IBAN_TR_RE = re.compile(r"\bTR\d{2}[0-9A-Z]{22}\b")

# Turkish company suffixes
_TR_COMPANY_SUFFIX = r"(?:A\.Ş\.|Ltd\.\s*Şti\.|Koll\.\s*Şti\.|Koop\.|T\.A\.Ş\.)"
# Middle tokens: connector OR capitalised word (including optional trailing dot for abbreviations)
_TR_NAME_TOKEN = r"(?:ve|ile|[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğışöşü]*\.?)"
COMPANY_NAME_TR_RE = re.compile(
    r"(?<![A-Za-zÇĞİÖŞÜçğışöşü])"
    r"("
    r"[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğışöşü]*"
    r"(?:\s+" + _TR_NAME_TOKEN + r"){0,6}"
    r"\s+" + _TR_COMPANY_SUFFIX + r")",
    re.UNICODE,
)

# MERSIS — Turkish company registry number, 16 digits, first digit non-zero
MERSIS_RE = re.compile(r"\b([1-9]\d{15})\b")

# Turkish postal codes: first 2 digits = province plate (01–81)
POSTAL_CODE_TR_RE = re.compile(r"\b((?:0[1-9]|[1-7]\d|80|81)\d{3})\b")

_TR_PROVINCES = [
    "Afyonkarahisar", "Kahramanmaraş", "Kırıkkale", "Kırklareli",
    "Diyarbakır", "Gaziantep", "Şanlıurfa", "Nevşehir",
    "Kastamonu", "Gümüşhane", "Eskişehir", "Erzincan",
    "Erzurum", "Denizli", "Çanakkale", "Adıyaman",
    "Zonguldak", "Tekirdağ", "Trabzon", "Tunceli",
    "Karaman", "Karabük", "Aksaray", "Antalya",
    "Kırşehir", "Osmaniye", "Kocaeli", "Sakarya",
    "Bartın", "Bayburt", "Ardahan", "Yozgat",
    "Ankara", "Amasya", "Artvin", "Balıkesir",
    "Bilecik", "Bingöl", "Bitlis", "Burdur",
    "Çankırı", "Edirne", "Elazığ", "Giresun",
    "Hakkari", "Isparta", "İstanbul", "İzmir",
    "Kayseri", "Kütahya", "Malatya", "Manisa",
    "Mardin", "Samsun", "Şırnak", "Sinop",
    "Tokat", "Hatay", "Konya", "Muğla",
    "Niğde", "Rize", "Siirt", "Sivas",
    "Adana", "Aydın", "Bursa", "Çorum",
    "Iğdır", "Kilis", "Mersin", "Batman",
    "Yalova", "Düzce", "Ordu", "Kars",
    "Ağrı", "Bolu", "Van", "Uşak", "Muş",
]
# Longest names first — prevents partial matches (e.g. "Kastamonu" before "Kars")
_TR_PROVINCES_SORTED = sorted(_TR_PROVINCES, key=len, reverse=True)
PROVINCE_TR_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in _TR_PROVINCES_SORTED) + r")\b",
    re.UNICODE,
)

# Label-prefixed name detection (TR and EN labels)
_NAME_PREFIX_TR = (
    r"(?:Ad[ıi]\s*(?:Soyad[ıi])?|Soyad[ıi]|İsim|"
    r"Müşteri\s+Ad[ıi]|Yetkili(?:\s+Kişi)?|Çalışan\s+Ad[ıi]|"
    r"Personel\s+Ad[ıi]|Kişi\s+Ad[ıi]|Satıcı\s+Ad[ıi]|"
    r"Alıcı\s+Ad[ıi]|İlgili\s+Kişi|Hesap\s+Sahibi)"
)
_NAME_PREFIX_EN = (
    r"(?:Full\s+Name|Customer\s+Name|Employee\s+Name|"
    r"Contact\s+Name|Authorized\s+(?:By|Person)|Account\s+Holder|"
    r"(?<!\bUser\s)Name)"
)
_NAME_VALUE = r"([A-ZÇĞİÖŞÜ][a-zçğışöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğışöşü]+){0,2})"
NAME_RE = re.compile(
    rf"(?:{_NAME_PREFIX_TR}|{_NAME_PREFIX_EN})\s*[:\-]\s*{_NAME_VALUE}",
    re.UNICODE,
)

# ── EU / International detectors ─────────────────────────────────────────────

# International IBAN — ISO 13616 country/length table, TR excluded.
# Country codes: EU member states + GB, CH, NO.
_IBAN_INTL_LENGTHS: dict[str, int] = {
    "AT": 20, "BE": 16, "BG": 22, "HR": 21, "CY": 28, "CZ": 24,
    "DK": 18, "EE": 20, "FI": 18, "FR": 27, "DE": 22, "GR": 27,
    "HU": 28, "IE": 22, "IT": 27, "LV": 21, "LT": 20, "LU": 20,
    "MT": 31, "NL": 18, "PL": 28, "PT": 25, "RO": 24, "SK": 24,
    "SI": 19, "ES": 24, "SE": 24, "GB": 22, "CH": 21, "NO": 15,
}
IBAN_INTL_RE = re.compile(r"\b([A-Z]{2}\d{2}[0-9A-Z]{11,30})\b")

# International company suffixes — longer patterns listed first to prevent partial matches.
# Latin Extended range (U+00C0–U+024F) covers German/French/Italian umlauts and accents.
_INTL_SUFFIX = (
    r"(?:KGaA|GmbH|OHG|GbR|SARL|EURL"
    r"|S\.p\.A\.|S\.r\.l\.|S\.n\.c\.|S\.a\.s\."
    r"|B\.V\.|N\.V\.|S\.A\.|S\.L\."
    r"|Corp\.|Inc\.|Ltd\.|LLP|LLC|PLC"
    r"|SpA|Srl|SNC|SAS|BV|NV|SL|SA"
    r"|Corp|Inc|Ltd|KG|AG|UG)"
)
_UC = r"[A-ZÀ-ɏ]"
_WC = r"[A-Za-z0-9À-ɏ\-]"
_INTL_NAME_TOKEN = rf"(?:and|&|{_UC}{_WC}*\.?)"
COMPANY_NAME_INTL_RE = re.compile(
    rf"(?<![A-Za-zÀ-ɏ])"
    rf"({_UC}{_WC}*"
    r"(?:\s+" + _INTL_NAME_TOKEN + r"){0,6}"
    r"\s+" + _INTL_SUFFIX + r")",
    re.UNICODE,
)

# ── US detectors ─────────────────────────────────────────────────────────────

# SSN — hyphens required to reduce false positives
SSN_RE = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
# EIN — employer identification: XX-XXXXXXX
EIN_US_RE = re.compile(r"\b(\d{2}-\d{7})\b")
# ITIN — individual TIN: 9XX-7X/8X/9X-XXXX
ITIN_US_RE = re.compile(r"\b(9\d{2}-(?:7[0-9]|8[0-8]|9[0-24-9])-\d{4})\b")

# ── DE detectors ──────────────────────────────────────────────────────────────
STEUER_ID_DE_RE = re.compile(r"\b([1-9]\d{10})\b")
SVNR_DE_RE = re.compile(r"\b(\d{4}[01]\d[0-3]\d[A-Z]\d{4})\b")

# ── FR detectors ──────────────────────────────────────────────────────────────
SIRET_FR_RE = re.compile(
    r"(?:SIRET|N°\s*SIRET|Num[eé]ro\s+SIRET|RCS)\s*[:#]*\s*(\d{14})\b",
    re.IGNORECASE,
)
SIREN_FR_RE = re.compile(
    r"(?:SIREN|N°\s*SIREN|Num[eé]ro\s+SIREN)\s*[:#]*\s*(\d{9})\b",
    re.IGNORECASE,
)
INSEE_FR_RE = re.compile(r"\b([12]\d{14})\b")

# ── IT detectors ──────────────────────────────────────────────────────────────
CODICE_FISCALE_IT_RE = re.compile(
    r"\b([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\b",
    re.IGNORECASE,
)
PARTITA_IVA_IT_RE = re.compile(r"\b(\d{11})\b")

# ── NL detectors ──────────────────────────────────────────────────────────────
BSN_NL_RE = re.compile(r"\b(\d{9})\b")
KVK_NL_RE = re.compile(
    r"(?:KVK|KvK|Handelsregister(?:nummer)?)\s*[:#]*\s*(\d{8})\b",
    re.IGNORECASE,
)

# ── ES detectors ──────────────────────────────────────────────────────────────
_DNI_LETTER_TABLE = "TRWAGMYFPDXBNJZSQVHLCKE"
DNI_ES_RE = re.compile(r"\b(\d{8}[A-Z])\b")
NIE_ES_RE = re.compile(r"\b([XYZ]\d{7}[A-Z])\b")
CIF_ES_RE = re.compile(r"\b([ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J])\b")

# ── UK detectors ──────────────────────────────────────────────────────────────
NI_UK_RE = re.compile(r"\b([A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\d{6}[ABCD])\b")
UTR_UK_RE = re.compile(
    r"(?:UTR|Unique\s+Taxpayer(?:\s+Reference)?)\s*[:#]*\s*(\d{10})\b",
    re.IGNORECASE,
)

# ── Validation helpers ────────────────────────────────────────────────────────


def _valid_tckn(s: str) -> bool:
    """TR Nüfus Müdürlüğü modular arithmetic checksum."""
    if len(s) != 11 or s[0] == "0":
        return False
    d = [int(c) for c in s]
    sum_odd = d[0] + d[2] + d[4] + d[6] + d[8]
    sum_even = d[1] + d[3] + d[5] + d[7]
    if (sum_odd * 7 - sum_even) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def _luhn(number: str) -> bool:
    """ISO/IEC 7812 Luhn checksum."""
    digits = [int(c) for c in number if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _valid_vkn(s: str) -> bool:
    """VKN Luhn-variant: weighted sum of first 9 digits, mod-9 reduction, checks 10th digit."""
    if len(s) != 10 or not s.isdigit() or s[0] == "0":
        return False
    d = [int(c) for c in s]
    total = 0
    for i in range(9):
        x = (d[i] + (9 - i)) % 10
        if x != 0:
            y = (x * (2 ** (9 - i))) % 9
            if y == 0:
                y = 9
        else:
            y = 0
        total += y
    return (10 - (total % 10)) % 10 == d[9]


def _valid_iban(s: str) -> bool:
    """ISO 7064 mod-97 IBAN checksum (all countries)."""
    rearranged = s[4:] + s[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged.upper())
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def _valid_iban_intl(s: str) -> bool:
    """ISO 13616: country existence, exact length, and mod-97 checksum. Excludes TR."""
    country = s[:2]
    if country == "TR" or country not in _IBAN_INTL_LENGTHS:
        return False
    if len(s) != _IBAN_INTL_LENGTHS[country]:
        return False
    return _valid_iban(s)


def _valid_phone_intl(raw: str) -> bool:
    """E.164: 7-15 total digits, excludes TR country code (+90)."""
    digits = re.sub(r"\D", "", raw)
    return 7 <= len(digits) <= 15 and digits[:2] != "90"


def _valid_steuer_id_de(s: str) -> bool:
    """ISO 7064 MOD 11,2 variant for German Steueridentifikationsnummer."""
    if len(s) != 11 or s[0] == "0":
        return False
    product = 10
    for i in range(10):
        total = (int(s[i]) + product) % 10
        if total == 0:
            total = 10
        product = (total * 2) % 11
    check = 11 - product
    if check == 10:
        check = 0
    return check == int(s[10])


def _valid_partita_iva_it(s: str) -> bool:
    """Italian Partita IVA checksum (Agenzia delle Entrate algorithm)."""
    if len(s) != 11 or not s.isdigit():
        return False
    odd_sum = sum(int(s[i]) for i in range(0, 10, 2))
    even_sum = 0
    for i in range(1, 10, 2):
        v = int(s[i]) * 2
        even_sum += v if v < 10 else v - 9
    return (10 - (odd_sum + even_sum) % 10) % 10 == int(s[10])


def _valid_bsn_nl(s: str) -> bool:
    """Dutch BSN 11-check: weighted sum (weights 9..2, -1) mod 11 == 0."""
    if len(s) != 9 or not s.isdigit():
        return False
    d = [int(c) for c in s]
    total = sum((9 - i) * d[i] for i in range(8)) - d[8]
    return total > 0 and total % 11 == 0


def _valid_dni_es(s: str) -> bool:
    """Spanish DNI: 8 digits + control letter = DNI_LETTER_TABLE[number % 23]."""
    if len(s) != 9 or not s[:8].isdigit():
        return False
    return _DNI_LETTER_TABLE[int(s[:8]) % 23] == s[8]


def _valid_nie_es(s: str) -> bool:
    """Spanish NIE: X/Y/Z prefix → 0/1/2 substitution, then DNI letter check."""
    if len(s) != 9 or s[0] not in "XYZ":
        return False
    prefix = {"X": "0", "Y": "1", "Z": "2"}[s[0]]
    return _DNI_LETTER_TABLE[int(prefix + s[1:8]) % 23] == s[8]


_NI_UK_FORBIDDEN = frozenset({"BG", "GB", "KN", "NK", "NT", "TN", "ZZ"})


def _valid_ni_uk(s: str) -> bool:
    """UK NI: reject HMRC-defined forbidden two-letter prefixes."""
    return s[:2].upper() not in _NI_UK_FORBIDDEN


_EIN_INVALID_PREFIXES = frozenset({
    "00", "07", "08", "09", "17", "18", "19", "28", "29",
    "49", "69", "70", "78", "79", "89", "96", "97",
})


def _valid_ein_us(s: str) -> bool:
    """US EIN: reject IRS-defined invalid area prefixes."""
    return s[:2] not in _EIN_INVALID_PREFIXES


# ── Locale registry ───────────────────────────────────────────────────────────

_LOCALE_DETECTORS: dict[str, set[str]] = {
    "tr": {
        "national_id_tr", "tax_id_tr", "phone_tr", "name",
        "iban_tr", "company_name_tr", "mersis_no", "postal_code_tr", "province_tr",
    },
    "us": {"ssn", "tax_id_us", "national_id_us", "phone_intl", "company_name_intl"},
    "eu": {"phone_intl", "iban_intl", "company_name_intl"},
    "de": {"tax_id_de", "social_id_de"},
    "fr": {"siret_fr", "company_id_fr", "social_id_fr"},
    "it": {"national_id_it", "tax_id_it"},
    "nl": {"national_id_nl", "company_id_nl"},
    "es": {"national_id_es", "tax_id_es"},
    "uk": {"social_id_uk", "tax_id_uk"},
}
_UNIVERSAL: set[str] = {"email", "iban", "credit_card", "ip", "ip_v6"}


def _active(locale: str) -> set[str]:
    if locale in ("all", "und"):
        active: set[str] = set(_UNIVERSAL)
        for detectors in _LOCALE_DETECTORS.values():
            active |= detectors
        return active
    return _UNIVERSAL | _LOCALE_DETECTORS.get(locale, set())


# ── Public detector ───────────────────────────────────────────────────────────


def detect_pii(text: str, locale: str = "und") -> list[dict]:
    """
    Detect PII in *text* and return findings sorted by position.

    Each finding: {"type": str, "value": str, "start": int, "end": int}

    Locale selectors:
        "und" — All detectors combined (default; use when language is unknown)
        "all" — Alias for "und"
        "tr"  — Turkish: TCKN, VKN, phone_tr, name, iban_tr, company_name_tr,
                mersis_no, postal_code_tr, province_tr
        "us"  — US: SSN, phone_intl, company_name_intl
        "eu"  — EU: phone_intl, iban_intl, company_name_intl
        "de" / "fr" / "it" / "nl" / "es" / "uk" — country-specific detectors
        Universal (always active): email, iban*, credit_card, ip, ip_v6
        * iban suppressed per-span when iban_tr or iban_intl fires.
    """
    active = _active(locale)
    findings: list[dict] = []
    t = text or ""

    if "email" in active:
        for m in EMAIL_RE.finditer(t):
            findings.append({"type": "email", "value": m.group(), "start": m.start(), "end": m.end()})

    if "phone_intl" in active:
        for m in PHONE_INTL_RE.finditer(t):
            candidate = m.group(1)
            if _valid_phone_intl(candidate):
                findings.append({"type": "phone_intl", "value": candidate, "start": m.start(1), "end": m.end(1)})

    if "iban" in active:
        for m in IBAN_RE.finditer(t):
            if _valid_iban(m.group(1)):
                findings.append({"type": "iban", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "credit_card" in active:
        for m in CC_RE.finditer(t):
            if _luhn(m.group()):
                findings.append({"type": "credit_card", "value": m.group(), "start": m.start(), "end": m.end()})

    if "ip" in active:
        for m in IPV4_RE.finditer(t):
            findings.append({"type": "ip", "value": m.group(), "start": m.start(), "end": m.end()})

    if "ip_v6" in active:
        for m in IPV6_RE.finditer(t):
            findings.append({"type": "ip_v6", "value": m.group(), "start": m.start(), "end": m.end()})

    if "phone_tr" in active:
        for m in PHONE_TR_RE.finditer(t):
            findings.append({"type": "phone_tr", "value": m.group(), "start": m.start(), "end": m.end()})

    if "national_id_tr" in active:
        for m in TCKN_RE.finditer(t):
            if _valid_tckn(m.group(1)):
                findings.append({"type": "national_id_tr", "value": m.group(1), "start": m.start(), "end": m.end()})

    if "tax_id_tr" in active:
        for m in VKN_RE.finditer(t):
            candidate = m.group(1)
            if _valid_vkn(candidate):
                findings.append({"type": "tax_id_tr", "value": candidate, "start": m.start(), "end": m.end()})

    if "name" in active:
        for m in NAME_RE.finditer(t):
            idx = m.lastindex
            findings.append({"type": "name", "value": m.group(idx), "start": m.start(idx), "end": m.end(idx)})

    if "iban_tr" in active:
        for m in IBAN_TR_RE.finditer(t):
            if _valid_iban(m.group()):
                findings.append({"type": "iban_tr", "value": m.group(), "start": m.start(), "end": m.end()})

    if "company_name_tr" in active:
        for m in COMPANY_NAME_TR_RE.finditer(t):
            findings.append({"type": "company_name_tr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "mersis_no" in active:
        for m in MERSIS_RE.finditer(t):
            findings.append({"type": "mersis_no", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "postal_code_tr" in active:
        for m in POSTAL_CODE_TR_RE.finditer(t):
            findings.append({"type": "postal_code_tr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "province_tr" in active:
        for m in PROVINCE_TR_RE.finditer(t):
            findings.append({"type": "province_tr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "ssn" in active:
        for m in SSN_RE.finditer(t):
            findings.append({"type": "ssn", "value": m.group(), "start": m.start(), "end": m.end()})

    if "tax_id_us" in active:
        for m in EIN_US_RE.finditer(t):
            if _valid_ein_us(m.group(1)):
                findings.append({"type": "tax_id_us", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "national_id_us" in active:
        for m in ITIN_US_RE.finditer(t):
            findings.append({"type": "national_id_us", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "tax_id_de" in active:
        for m in STEUER_ID_DE_RE.finditer(t):
            if _valid_steuer_id_de(m.group(1)):
                findings.append({"type": "tax_id_de", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "social_id_de" in active:
        for m in SVNR_DE_RE.finditer(t):
            findings.append({"type": "social_id_de", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "siret_fr" in active:
        for m in SIRET_FR_RE.finditer(t):
            findings.append({"type": "siret_fr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "company_id_fr" in active:
        for m in SIREN_FR_RE.finditer(t):
            findings.append({"type": "company_id_fr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "social_id_fr" in active:
        for m in INSEE_FR_RE.finditer(t):
            findings.append({"type": "social_id_fr", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "national_id_it" in active:
        for m in CODICE_FISCALE_IT_RE.finditer(t):
            findings.append({"type": "national_id_it", "value": m.group(1).upper(), "start": m.start(1), "end": m.end(1)})

    if "tax_id_it" in active:
        for m in PARTITA_IVA_IT_RE.finditer(t):
            if _valid_partita_iva_it(m.group(1)):
                findings.append({"type": "tax_id_it", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "national_id_nl" in active:
        for m in BSN_NL_RE.finditer(t):
            if _valid_bsn_nl(m.group(1)):
                findings.append({"type": "national_id_nl", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "company_id_nl" in active:
        for m in KVK_NL_RE.finditer(t):
            findings.append({"type": "company_id_nl", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "national_id_es" in active:
        for m in DNI_ES_RE.finditer(t):
            if _valid_dni_es(m.group(1)):
                findings.append({"type": "national_id_es", "value": m.group(1), "start": m.start(1), "end": m.end(1)})
        for m in NIE_ES_RE.finditer(t):
            if _valid_nie_es(m.group(1)):
                findings.append({"type": "national_id_es", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "tax_id_es" in active:
        for m in CIF_ES_RE.finditer(t):
            findings.append({"type": "tax_id_es", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "social_id_uk" in active:
        for m in NI_UK_RE.finditer(t):
            if _valid_ni_uk(m.group(1)):
                findings.append({"type": "social_id_uk", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "tax_id_uk" in active:
        for m in UTR_UK_RE.finditer(t):
            findings.append({"type": "tax_id_uk", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    if "iban_intl" in active:
        for m in IBAN_INTL_RE.finditer(t):
            candidate = m.group(1)
            if _valid_iban_intl(candidate):
                findings.append({"type": "iban_intl", "value": candidate, "start": m.start(1), "end": m.end(1)})

    if "company_name_intl" in active:
        for m in COMPANY_NAME_INTL_RE.finditer(t):
            findings.append({"type": "company_name_intl", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    findings.sort(key=lambda x: x["start"])

    # Dedup: where a specific iban_tr or iban_intl covers the same span as a
    # generic iban finding, drop the generic one to avoid duplicate entries.
    specific_iban_spans = {
        (f["start"], f["end"]) for f in findings if f["type"] in ("iban_tr", "iban_intl")
    }
    if specific_iban_spans:
        findings = [
            f for f in findings
            if not (f["type"] == "iban" and (f["start"], f["end"]) in specific_iban_spans)
        ]

    return findings
