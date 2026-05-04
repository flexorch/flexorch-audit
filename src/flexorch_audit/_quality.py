def quality_metrics(text: str) -> dict:
    """
    Compute quality metrics for a single text record.

    Returns:
        completeness    — 1.0 if text is non-empty after stripping whitespace, else 0.0
        avg_length      — character count of stripped text
        duplicate_ratio — always None for single-record input; compute across your
                          full dataset by comparing audit() results per record
    """
    stripped = (text or "").strip()
    return {
        "completeness": 1.0 if stripped else 0.0,
        "avg_length": len(stripped),
        "duplicate_ratio": None,
    }
