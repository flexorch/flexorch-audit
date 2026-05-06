"""
flexorch-audit — zero-dependency PII + quality + noise audit for LLM datasets.

    from flexorch_audit import audit, mask

    text = open("contract.txt").read()
    result = audit(text, locale="tr")

    result.quality_grade   # "A"
    result.quality_score   # 0.91
    result.pii_summary     # [{"type": "national_id_tr", "count": 3}, ...]

    # Dict-style access also works (backwards compatible):
    result["pii"]          # [{type, value, start, end}, ...]
    result["quality"]      # {completeness, avg_length, duplicate_ratio}
    result["noise"]        # {garbage_ratio, encoding_ok}

    clean = mask(text, result["pii"], strategy="redact")
"""

from collections import Counter

from ._pii import detect_pii
from ._quality import quality_metrics
from ._noise import noise_metrics
from ._mask import apply_mask

__version__ = "0.2.0"
__all__ = ["audit", "mask", "AuditResult", "__version__"]


class AuditResult(dict):
    """
    Audit result returned by audit().

    Supports both dict-style access (result["pii"]) and attribute access
    (result.quality_grade) for convenience.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"AuditResult has no attribute {name!r}")

    def __repr__(self) -> str:
        grade = self.get("quality_grade", "?")
        score = self.get("quality_score", 0.0)
        n_pii = len(self.get("pii", []))
        return f"AuditResult(grade={grade!r}, score={score}, pii_count={n_pii})"


def _compute_quality_score(completeness: float, avg_length: int, garbage_ratio: float) -> float:
    """Composite quality score (0.0–1.0) from completeness, length, and noise."""
    length_score = min(avg_length / 500, 1.0)
    noise_score = max(0.0, 1.0 - garbage_ratio * 10)
    return round(completeness * (0.4 * noise_score + 0.4 * length_score + 0.2), 4)


def _compute_quality_grade(score: float) -> str:
    """Map quality score to A/B/C/D letter grade."""
    if score >= 0.85:
        return "A"
    if score >= 0.65:
        return "B"
    if score >= 0.40:
        return "C"
    return "D"


def audit(text: str, locale: str = "tr") -> AuditResult:
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
        AuditResult (dict subclass) with:
            quality_grade  — "A" | "B" | "C" | "D" overall LLM-readiness grade
            quality_score  — 0.0–1.0 composite score (completeness + length + noise)
            pii_summary    — [{type, count}] PII findings aggregated by type
            pii            — [{type, value, start, end}] raw findings sorted by position
            quality        — {completeness, avg_length, duplicate_ratio}
            noise          — {garbage_ratio, encoding_ok}
    """
    pii = detect_pii(text, locale=locale)
    quality = quality_metrics(text)
    noise = noise_metrics(text)

    quality_score = _compute_quality_score(
        quality["completeness"],
        quality["avg_length"],
        noise["garbage_ratio"],
    )
    quality_grade = _compute_quality_grade(quality_score)

    counts = Counter(f["type"] for f in pii)
    pii_summary = [{"type": t, "count": c} for t, c in sorted(counts.items())]

    return AuditResult(
        quality_grade=quality_grade,
        quality_score=quality_score,
        pii_summary=pii_summary,
        pii=pii,
        quality=quality,
        noise=noise,
    )


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
