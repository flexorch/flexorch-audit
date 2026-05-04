from flexorch_audit._noise import noise_metrics


def test_clean_text():
    result = noise_metrics("Hello, world!")
    assert result["garbage_ratio"] == 0.0
    assert result["encoding_ok"] is True


def test_empty_string():
    result = noise_metrics("")
    assert result["garbage_ratio"] == 0.0
    assert result["encoding_ok"] is True


def test_none_treated_as_empty():
    result = noise_metrics(None)  # type: ignore[arg-type]
    assert result["garbage_ratio"] == 0.0
    assert result["encoding_ok"] is True


def test_encoding_error_detected():
    text = "Normal text � with replacement char"
    result = noise_metrics(text)
    assert result["encoding_ok"] is False
    assert result["garbage_ratio"] > 0.0


def test_control_characters_counted():
    # \x01 is a control character (Cc category), not normal whitespace
    text = "abc\x01def"
    result = noise_metrics(text)
    assert result["garbage_ratio"] > 0.0


def test_normal_whitespace_not_garbage():
    text = "line one\nline two\ttabbed"
    result = noise_metrics(text)
    assert result["garbage_ratio"] == 0.0


def test_high_garbage_text():
    text = "\x00\x01\x02\x03\x04\x05"
    result = noise_metrics(text)
    assert result["garbage_ratio"] == 1.0


def test_unicode_text_no_garbage():
    result = noise_metrics("Türkçe metin: Çiğdem, Şükrü, İstanbul")
    assert result["garbage_ratio"] == 0.0
    assert result["encoding_ok"] is True
