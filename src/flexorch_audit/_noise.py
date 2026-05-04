import unicodedata

# Unicode general categories that indicate non-printable / garbage characters.
# Cc=control, Cs=surrogate, Co=private-use, Cn=unassigned
_GARBAGE_CATS = frozenset({"Cc", "Cs", "Co", "Cn"})

# Normal whitespace is not garbage even though it falls in Cc
_SAFE_WHITESPACE = frozenset(" \t\n\r\x0b\x0c")


def _is_garbage(ch: str) -> bool:
    if ch in _SAFE_WHITESPACE:
        return False
    return unicodedata.category(ch) in _GARBAGE_CATS or ch == "�"


def noise_metrics(text: str) -> dict:
    """
    Compute noise metrics for a single text record.

    Returns:
        garbage_ratio — fraction of characters that are control/private/unassigned
                        or Unicode replacement characters (U+FFFD)
        encoding_ok   — False when U+FFFD replacement characters are present,
                        which typically indicates a transcoding error
    """
    if not text:
        return {"garbage_ratio": 0.0, "encoding_ok": True}

    n = len(text)
    garbage = sum(1 for ch in text if _is_garbage(ch))
    return {
        "garbage_ratio": round(garbage / n, 4),
        "encoding_ok": "�" not in text,
    }
