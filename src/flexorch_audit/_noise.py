import re
import unicodedata

# Unicode general categories that indicate non-printable / garbage characters.
# Cc=control, Cs=surrogate, Co=private-use, Cn=unassigned
_GARBAGE_CATS = frozenset({"Cc", "Cs", "Co", "Cn"})

# Normal whitespace is not garbage even though it falls in Cc
_SAFE_WHITESPACE = frozenset(" \t\n\r\x0b\x0c")

# Line-level noise: 3+ consecutive special chars (matches core FlexOrch pipeline)
_LINE_NOISE_RE = re.compile(r"[@#!~*=]{3,}")


def _is_garbage(ch: str) -> bool:
    if ch in _SAFE_WHITESPACE:
        return False
    return unicodedata.category(ch) in _GARBAGE_CATS or ch == "�"


def noise_ratio(text: str) -> float:
    """
    Fraction of lines that are empty or contain garbage symbol patterns.

    A line is noisy when it is blank (after strip) or contains 3+ consecutive
    special characters from the set ``@ # ! ~ * =``.  This mirrors the
    FlexOrch pipeline quality-step penalty threshold.

    Returns a float in [0.0, 1.0].  Values above 0.20 indicate a document
    likely to reduce extraction quality.
    """
    if not text:
        return 0.0
    lines = text.splitlines()
    total = len(lines)
    if total == 0:
        return 0.0
    noisy = sum(1 for line in lines if not line.strip() or _LINE_NOISE_RE.search(line))
    return round(noisy / total, 4)


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
