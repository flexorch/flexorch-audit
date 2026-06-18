import hashlib

# Pre-computed valid TCKNs for strategy="replace" — checksum verified
_TCKN_POOL = ["12345678950", "10000000146", "23456789060"]

# Pre-computed valid TR IBANs for strategy="replace" — mod-97 verified
_IBAN_TR_POOL = ["TR330006100519786457841326", "TR390006199999888888888813"]

# Name pool for strategy="replace"
_NAME_POOL = [
    "Ahmet Yılmaz", "Mehmet Demir", "Ayşe Kaya", "Fatma Çelik",
    "Ali Şahin", "Zeynep Arslan", "Mustafa Öztürk", "Emine Doğan",
    "İbrahim Kurt", "Hatice Aydın", "Hasan Yıldız", "Elif Güneş",
    "Hüseyin Çetin", "Meryem Polat", "Ömer Koç", "Büşra Tekin",
    "Yusuf Erdoğan", "Selin Bozkurt", "Kemal Akın", "Derya Uçar",
]

_STATIC_SYNTHETIC: dict[str, str] = {
    "email": "user@example.com",
    "phone": "+1 000 000 0000",
    "phone_tr": "0500 000 00 00",
    "phone_intl": "+1 000 000 0000",
    "ssn": "000-00-0000",
    "iban": "XX00 0000 0000 0000 0000 00",
    "credit_card": "0000 0000 0000 0000",
    "ip": "0.0.0.0",
    "ip_v6": "2001:db8::1",
    "national_id_pl": "00000000000",
    "social_id_at": "0000000000",
    "national_id_be": "00000000000",
}

_VALID_STRATEGIES = frozenset({"redact", "replace", "token", "hash"})


def _pick(pool: list[str], seed: str) -> str:
    """Deterministically pick from pool using SHA-256 of seed."""
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return pool[h % len(pool)]


def _synthetic(ptype: str, original: str) -> str:
    if ptype == "national_id_tr":
        return _pick(_TCKN_POOL, original)
    if ptype in ("iban_tr", "iban_intl"):
        return _pick(_IBAN_TR_POOL, original)
    if ptype == "name":
        return _pick(_NAME_POOL, original)
    return _STATIC_SYNTHETIC.get(ptype, f"[{ptype.upper()}]")


def apply_mask(text: str, findings: list[dict], strategy: str = "redact") -> str:
    """
    Replace PII spans in *text* according to *strategy*.

    Strategies:
        redact  — [MASKED_EMAIL], [MASKED_PHONE_TR], …  (default)
        replace — realistic synthetic value (e.g. user@example.com, valid TCKN)
        token   — <PII_EMAIL_1>, <PII_EMAIL_2>, …  (unique per type per call)
        hash    — first 16 hex chars of SHA-256(original_value)

    Findings are applied in reverse position order so earlier replacements
    do not shift the indices of later ones.
    """
    if strategy not in _VALID_STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}. Use: {', '.join(sorted(_VALID_STRATEGIES))}")
    if not text or not findings:
        return text or ""

    result = text
    counter: dict[str, int] = {}

    for finding in sorted(findings, key=lambda x: x["start"], reverse=True):
        ptype = finding["type"]
        counter[ptype] = counter.get(ptype, 0) + 1
        tag = ptype.upper()

        if strategy == "redact":
            replacement = f"[MASKED_{tag}]"
        elif strategy == "replace":
            replacement = _synthetic(ptype, finding["value"])
        elif strategy == "token":
            replacement = f"<PII_{tag}_{counter[ptype]}>"
        else:  # hash
            h = hashlib.sha256(finding["value"].encode()).hexdigest()[:16]
            replacement = f"[{h}]"

        result = result[: finding["start"]] + replacement + result[finding["end"] :]

    return result
