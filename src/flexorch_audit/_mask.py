import hashlib

# Realistic-looking synthetic replacements for strategy="replace"
_SYNTHETIC: dict[str, str] = {
    "email": "user@example.com",
    "phone": "+1 000 000 0000",
    "phone_tr": "0500 000 00 00",
    "national_id_tr": "00000000000",
    "ssn": "000-00-0000",
    "iban": "XX00 0000 0000 0000 0000 00",
    "credit_card": "0000 0000 0000 0000",
    "ip": "0.0.0.0",
    "name": "AD SOYAD",
}

_VALID_STRATEGIES = frozenset({"redact", "replace", "token", "hash"})


def apply_mask(text: str, findings: list[dict], strategy: str = "redact") -> str:
    """
    Replace PII spans in *text* according to *strategy*.

    Strategies:
        redact  — [REDACTED_EMAIL], [REDACTED_PHONE_TR], …  (default)
        replace — realistic synthetic value (e.g. user@example.com)
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
            replacement = f"[REDACTED_{tag}]"
        elif strategy == "replace":
            replacement = _SYNTHETIC.get(ptype, f"[{tag}]")
        elif strategy == "token":
            replacement = f"<PII_{tag}_{counter[ptype]}>"
        else:  # hash
            h = hashlib.sha256(finding["value"].encode()).hexdigest()[:16]
            replacement = f"[{h}]"

        result = result[: finding["start"]] + replacement + result[finding["end"] :]

    return result
