"""
flexorch-audit — zero-dependency PII + quality + noise audit for LLM datasets.

    from flexorch_audit import audit, mask

    result = audit(text, locale="tr")
    # {
    #   "pii": [{"type": "email", "value": "...", "start": 5, "end": 22}, ...],
    #   "quality": {"completeness": 1.0, "avg_length": 342, "duplicate_ratio": None},
    #   "noise": {"garbage_ratio": 0.0, "encoding_ok": True},
    # }

    clean = mask(text, result["pii"], strategy="redact")
"""

from ._pii import detect_pii
from ._quality import quality_metrics
from ._noise import noise_metrics
from ._mask import apply_mask

__version__ = "0.1.0"
__all__ = ["audit", "mask", "__version__"]


def audit(text: str, locale: str = "tr") -> dict:
    """
    Audit *text* for LLM dataset readiness.

    Args:
        text:   Raw text to analyse.
        locale: Which locale-specific detectors to activate.
                "tr"  — Turkish: TCKN, phone_tr, name  (default)
                "us"  — US: SSN, E.164 phone
                "eu"  — EU: E.164 phone
                "all" — All detectors (phone_tr takes precedence over generic phone)
                Universal detectors (email, iban, credit_card, ip) are always active.

    Returns:
        {
            "pii":     list of {type, value, start, end} sorted by position,
            "quality": {completeness, avg_length, duplicate_ratio},
            "noise":   {garbage_ratio, encoding_ok},
        }
    """
    return {
        "pii": detect_pii(text, locale=locale),
        "quality": quality_metrics(text),
        "noise": noise_metrics(text),
    }


def mask(text: str, findings: list[dict], strategy: str = "redact") -> str:
    """
    Apply masking to PII findings in *text*.

    Args:
        text:     Original text.
        findings: List of findings from audit()["pii"].
        strategy: "redact" (default) | "replace" | "token" | "hash"

    Returns:
        Text with PII replaced according to *strategy*.
    """
    return apply_mask(text, findings, strategy)
