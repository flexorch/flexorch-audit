"""
flexorch-audit — zero-dependency PII + quality + noise audit for LLM datasets.

    from flexorch_audit import audit, mask

    text = open("contract.txt").read()
    result = audit(text)               # locale defaults to "und" (all detectors)
    result = audit(text, locale="tr")  # Turkish-only detectors

    result.quality_grade      # "A"
    result.quality_score      # 0.91
    result.noise_ratio        # 0.03  (line-level noise fraction)
    result.detected_language  # "und" (locale passed in — caller controls language)
    result.pii_summary        # [{"type": "national_id_tr", "count": 3}, ...]

    # Dict-style access also works (backwards compatible):
    result["pii"]          # [{type, value, start, end}, ...]
    result["quality"]      # {completeness, avg_length, duplicate_ratio}
    result["noise"]        # {garbage_ratio, encoding_ok}

    clean = mask(text, result["pii"], strategy="redact")
"""

from __future__ import annotations

import asyncio
from collections import Counter
from typing import AsyncGenerator, AsyncIterable

from ._pii import detect_pii
from ._quality import quality_metrics
from ._noise import noise_metrics, noise_ratio as _noise_ratio
from ._mask import apply_mask

__version__ = "0.8.2"
__all__ = ["audit", "audit_batch", "audit_stream", "mask", "redact_for_llm", "estimate_tokens", "compliance_report", "AuditResult", "__version__"]


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


def audit(text: str, locale: str = "und") -> AuditResult:
    """
    Audit *text* for LLM dataset readiness.

    Args:
        text:   Raw text to analyse.
        locale: Which locale-specific detectors to activate.
                "und" — All detectors combined (default; use when language is unknown)
                "all" — Alias for "und"
                "tr"  — Turkish: TCKN, VKN, phone_tr, name, iban_tr,
                        company_name_tr, mersis_no, postal_code_tr, province_tr
                "us"  — US: SSN, phone_intl, company_name_intl
                "eu"  — EU: phone_intl, iban_intl, company_name_intl
                "de" / "fr" / "it" / "nl" / "es" / "uk" — country-specific detectors
                Universal (always active): email, iban*, credit_card, ip, ip_v6
                * iban is suppressed per-span when iban_tr or iban_intl fires.

    Returns:
        AuditResult (dict subclass) with:
            quality_grade     — "A" | "B" | "C" | "D" overall LLM-readiness grade
            quality_score     — 0.0–1.0 composite score (completeness + length + noise)
            pii_summary       — [{type, count}] PII findings aggregated by type
            pii               — [{type, value, start, end}] raw findings sorted by position
            quality           — {completeness, avg_length, duplicate_ratio}
            noise             — {garbage_ratio, encoding_ok}
            noise_ratio       — fraction of lines that are blank or contain symbol noise (>0.20 = low quality)
            detected_language — the locale value passed in (caller is responsible for language detection)
    """
    pii = detect_pii(text, locale=locale)
    quality = quality_metrics(text)
    noise = noise_metrics(text)
    nr = _noise_ratio(text)

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
        noise_ratio=nr,
        detected_language=locale,
    )


def audit_batch(texts: list[str], locale: str = "und") -> dict:
    """
    Audit a list of texts and aggregate metrics — including duplicate_ratio.

    Args:
        texts:  List of raw texts to analyse.
        locale: Same locale selector as audit().

    Returns:
        results           — list[AuditResult], one per input text
        duplicate_ratio   — fraction of texts that are exact duplicates
        pii_summary       — aggregated PII counts across all texts
        avg_quality_score — mean quality_score across all texts
    """
    if not texts:
        return {
            "results": [],
            "duplicate_ratio": 0.0,
            "pii_summary": [],
            "avg_quality_score": 0.0,
        }

    results = [audit(t, locale=locale) for t in texts]

    seen: set[str] = set()
    dup_count = 0
    for t in texts:
        if t in seen:
            dup_count += 1
        else:
            seen.add(t)
    dup_ratio = round(dup_count / len(texts), 4)

    all_pii: list[dict] = []
    for r in results:
        all_pii.extend(r["pii"])
    counts = Counter(f["type"] for f in all_pii)
    pii_summary = [{"type": t, "count": c} for t, c in sorted(counts.items())]

    avg_score = round(sum(r.quality_score for r in results) / len(results), 4)

    return {
        "results": results,
        "duplicate_ratio": dup_ratio,
        "pii_summary": pii_summary,
        "avg_quality_score": avg_score,
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


async def audit_stream(
    texts: AsyncIterable[str],
    locale: str = "und",
) -> AsyncGenerator[AuditResult, None]:
    """
    Async generator that audits texts one at a time from an async iterable.

    Yields one AuditResult per input text. Processing is sequential — for
    CPU-bound parallelism use asyncio.to_thread() or a thread pool externally.

    Args:
        texts:  Async iterable of raw text strings (e.g. async file reader).
        locale: Same locale selector as audit().

    Example::

        async def lines():
            for line in open("data.txt"):
                yield line

        async for result in audit_stream(lines()):
            print(result.quality_grade, result.pii_summary)
    """
    async for text in texts:
        yield await asyncio.to_thread(audit, text, locale)


def redact_for_llm(text: str, locale: str = "und", strategy: str = "redact") -> str:
    """
    Audit *text* and return a PII-free version ready for LLM processing.

    One-shot convenience wrapper around audit() + mask(). Equivalent to:
        result = audit(text, locale=locale)
        return mask(text, result["pii"], strategy=strategy)

    Args:
        text:     Raw text to clean.
        locale:   Same locale selector as audit() — default "und" (all detectors).
        strategy: Masking strategy passed to mask() — "redact" (default) | "replace" | "token" | "hash"

    Returns:
        Text with all detected PII replaced according to *strategy*.
        Returns the original text unchanged when no PII is found.

    Example::

        clean = redact_for_llm("TCKN: 12345678950, email: ali@example.com", locale="tr")
        # "TCKN: [MASKED_NATIONAL_ID_TR], email: [MASKED_EMAIL]"
    """
    result = audit(text, locale=locale)
    return mask(text, result["pii"], strategy=strategy)


def estimate_tokens(text: str) -> int:
    """
    Estimate the token count of *text* using a word-based heuristic.

    Uses the standard approximation: 1 token ≈ 0.75 words (words × 4/3).
    No external dependencies — accuracy within ~15% of tiktoken for English
    and most European languages. Turkish may run slightly higher due to
    agglutination; treat as a planning estimate, not an exact count.

    Args:
        text: Raw text to estimate.

    Returns:
        Estimated token count (int ≥ 0).

    Example::

        estimate_tokens("The quick brown fox")   # → 7
        estimate_tokens("")                       # → 0
    """
    if not text or not text.strip():
        return 0
    return max(1, round(len(text.split()) * 4 / 3))


_HIGH_RISK_TYPES = frozenset({
    "national_id_tr", "ssn", "credit_card",
    "national_id_pl", "national_id_be", "social_id_at",
    "social_id_de", "social_id_uk", "national_id_it",
    "national_id_nl", "national_id_es", "national_id_us",
    "tax_id_tr", "tax_id_de",
})

_MEDIUM_RISK_TYPES = frozenset({
    "email", "phone_tr", "phone_intl", "iban", "iban_tr", "iban_intl", "name",
})


def compliance_report(result: AuditResult) -> dict:
    """
    Generate a KVKK/GDPR compliance summary for an AuditResult.

    This is a technical summary only — not a legal document or regulatory opinion.

    Args:
        result: AuditResult returned by audit().

    Returns:
        has_pii          — bool: True if any PII was detected
        pii_types        — list[str]: unique PII types found, sorted
        risk_level       — "none" | "low" | "medium" | "high"
        masking_required — bool: True when has_pii
        recommendations  — list[str]: actionable next steps
    """
    pii = result.get("pii", [])
    types = sorted({f["type"] for f in pii})

    if not types:
        level = "none"
    elif any(t in _HIGH_RISK_TYPES for t in types):
        level = "high"
    elif any(t in _MEDIUM_RISK_TYPES for t in types):
        level = "medium"
    else:
        level = "low"

    recs: list[str] = []
    if level in ("high", "medium"):
        recs.append("Apply mask(strategy='redact') before storing or sharing this text.")
    if level == "high":
        recs.append(
            "Review applicable regulations (KVKK Art. 6, GDPR Art. 9) "
            "for special category data handling."
        )
    if not recs:
        recs.append("No PII detected — text is safe for LLM processing.")

    return {
        "has_pii": bool(types),
        "pii_types": types,
        "risk_level": level,
        "masking_required": bool(types),
        "recommendations": recs,
    }
