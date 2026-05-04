from flexorch_audit._quality import quality_metrics


def test_non_empty_text():
    result = quality_metrics("Hello, world!")
    assert result["completeness"] == 1.0
    assert result["avg_length"] == 13
    assert result["duplicate_ratio"] is None


def test_empty_string():
    result = quality_metrics("")
    assert result["completeness"] == 0.0
    assert result["avg_length"] == 0


def test_whitespace_only():
    result = quality_metrics("   \t\n  ")
    assert result["completeness"] == 0.0
    assert result["avg_length"] == 0


def test_strips_leading_trailing_whitespace():
    result = quality_metrics("  hello  ")
    assert result["avg_length"] == 5


def test_none_treated_as_empty():
    result = quality_metrics(None)  # type: ignore[arg-type]
    assert result["completeness"] == 0.0
    assert result["avg_length"] == 0


def test_long_text():
    text = "a" * 10_000
    result = quality_metrics(text)
    assert result["completeness"] == 1.0
    assert result["avg_length"] == 10_000
