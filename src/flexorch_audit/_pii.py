import re

# ── Universal detectors ──────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# E.164 international phone — requires + prefix, 10+ total digits
# Used for locale=us/eu. TR phones covered by PHONE_TR_RE.
PHONE_INTL_RE = re.compile(
    r"\+\d{1,3}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{3,4}[\s\-\.]?\d{4}\b"
)

# IBAN — ISO 13616 (all countries, including TR)
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[0-9A-Z]{11,30}\b")

# Credit card — 16 digits with separator groups (Luhn-validated separately)
CC_RE = re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")

# IPv4
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# ── Turkish detectors ────────────────────────────────────────────────────────

# Turkish mobile: +90 5xx... or 0 5xx... or bare 5xx (10 digits)
PHONE_TR_RE = re.compile(r"\b(?:\+90|0)?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}\b")

# TCKN — first digit non-zero, 11 digits, checksum-validated below
TCKN_RE = re.compile(r"\b([1-9]\d{10})\b")

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

# Label-prefixed name detection (TR and EN labels). NLP-based free-standing name
# detection is out of scope for v0.1 — requires NER.
NAME_RE = re.compile(
    rf"(?:{_NAME_PREFIX_TR}|{_NAME_PREFIX_EN})\s*[:\-]\s*{_NAME_VALUE}",
    re.UNICODE,
)

# ── US detectors ─────────────────────────────────────────────────────────────

# SSN — hyphens required to minimise false positives
SSN_RE = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")

# ── Validation helpers ────────────────────────────────────────────────────────


def _valid_tckn(s: str) -> bool:
    # TR Nüfus Müdürlüğü modular arithmetic — same as Luhn-family checksums
    if len(s) != 11 or s[0] == "0":
        return False
    d = [int(c) for c in s]
    sum_odd = d[0] + d[2] + d[4] + d[6] + d[8]
    sum_even = d[1] + d[3] + d[5] + d[7]
    if (sum_odd * 7 - sum_even) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def _luhn(number: str) -> bool:
    # ISO/IEC 7812 Luhn checksum
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


# ── Locale registry ───────────────────────────────────────────────────────────

_LOCALE_DETECTORS: dict[str, set[str]] = {
    "tr": {"national_id_tr", "phone_tr", "name"},
    "us": {"ssn", "phone"},
    "eu": {"phone"},
}
_UNIVERSAL: set[str] = {"email", "iban", "credit_card", "ip"}


def _active(locale: str) -> set[str]:
    if locale == "all":
        active: set[str] = set(_UNIVERSAL)
        for detectors in _LOCALE_DETECTORS.values():
            active |= detectors
        # phone_tr is more specific than generic phone; skip generic when both active
        if "phone_tr" in active:
            active.discard("phone")
        return active
    return _UNIVERSAL | _LOCALE_DETECTORS.get(locale, set())


# ── Public detector ───────────────────────────────────────────────────────────


def detect_pii(text: str, locale: str = "tr") -> list[dict]:
    """
    Detect PII in *text* and return a list of findings sorted by position.

    Each finding: {"type": str, "value": str, "start": int, "end": int}
    """
    active = _active(locale)
    findings: list[dict] = []
    t = text or ""

    if "email" in active:
        for m in EMAIL_RE.finditer(t):
            findings.append({"type": "email", "value": m.group(), "start": m.start(), "end": m.end()})

    if "phone" in active:
        for m in PHONE_INTL_RE.finditer(t):
            if sum(c.isdigit() for c in m.group()) >= 10:
                findings.append({"type": "phone", "value": m.group(), "start": m.start(), "end": m.end()})

    if "iban" in active:
        for m in IBAN_RE.finditer(t):
            findings.append({"type": "iban", "value": m.group(), "start": m.start(), "end": m.end()})

    if "credit_card" in active:
        for m in CC_RE.finditer(t):
            if _luhn(m.group()):
                findings.append({"type": "credit_card", "value": m.group(), "start": m.start(), "end": m.end()})

    if "ip" in active:
        for m in IPV4_RE.finditer(t):
            findings.append({"type": "ip", "value": m.group(), "start": m.start(), "end": m.end()})

    if "phone_tr" in active:
        for m in PHONE_TR_RE.finditer(t):
            findings.append({"type": "phone_tr", "value": m.group(), "start": m.start(), "end": m.end()})

    if "national_id_tr" in active:
        for m in TCKN_RE.finditer(t):
            if _valid_tckn(m.group(1)):
                findings.append({"type": "national_id_tr", "value": m.group(1), "start": m.start(), "end": m.end()})

    if "name" in active:
        for m in NAME_RE.finditer(t):
            idx = m.lastindex
            findings.append({"type": "name", "value": m.group(idx), "start": m.start(idx), "end": m.end(idx)})

    if "ssn" in active:
        for m in SSN_RE.finditer(t):
            findings.append({"type": "ssn", "value": m.group(), "start": m.start(), "end": m.end()})

    findings.sort(key=lambda x: x["start"])
    return findings
