from flexorch_audit._noise import noise_metrics, noise_ratio


# ── noise_ratio (line-based) ─────────────────────────────────────────────────

def test_noise_ratio_empty():
    assert noise_ratio("") == 0.0


def test_noise_ratio_clean():
    assert noise_ratio("Hello\nworld\nno noise here") == 0.0


def test_noise_ratio_blank_lines():
    text = "line1\n\n\nline4"  # 2 blank lines out of 4
    assert noise_ratio(text) == 0.5


def test_noise_ratio_symbol_noise():
    text = "normal line\n@@@garbage\n===another\nclean"
    # 2 noisy lines out of 4
    assert noise_ratio(text) == 0.5


def test_noise_ratio_below_threshold():
    text = "\n".join(["clean line"] * 10)
    assert noise_ratio(text) == 0.0


def test_noise_ratio_above_threshold():
    text = "\n".join(["@@@"] * 30 + ["clean"] * 10)
    assert noise_ratio(text) == 0.75


def test_noise_ratio_mixed():
    # blank line + symbol line + clean line + clean line = 2 noisy out of 4 = 0.5
    text = "\n@@@\nclean\nclean"
    assert noise_ratio(text) == 0.5


# ── noise_metrics (character-based) ─────────────────────────────────────────

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
