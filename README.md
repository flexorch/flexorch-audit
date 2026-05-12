# flexorch-audit

[![PyPI](https://img.shields.io/pypi/v/flexorch-audit)](https://pypi.org/project/flexorch-audit/)
[![Python](https://img.shields.io/pypi/pyversions/flexorch-audit)](https://pypi.org/project/flexorch-audit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Zero-dependency PII detection, quality grading, and noise audit for LLM datasets — in a single function call.

## Why

Before feeding documents into an LLM pipeline you need to answer three questions:

1. **Does this text contain personal data?** Sending PII to a language model is a compliance risk.
2. **Is the text quality high enough?** Short, noisy, or duplicate records hurt fine-tuning and RAG retrieval.
3. **How bad is the noise?** Garbled encodings and control characters degrade model output silently.

Most tools that answer these questions require heavy NLP frameworks, model weights, or cloud APIs. `flexorch-audit` answers all three with one call — using only regex and Python's standard library. No model weights, no network calls, no external packages.

## Features

- **Quality grade** — A/B/C/D composite score: is this text LLM-ready at a glance?
- **PII detection** — email, phone (TR mobile + E.164), credit card (Luhn), IPv4, IPv6, TCKN, VKN, IBAN (mod-97 validated), SSN, label-prefixed names
- **Batch audit** — `audit_batch()` aggregates duplicate ratio and PII counts across an entire dataset in one call
- **Noise metrics** — garbage character ratio, encoding health check
- **Masking** — four strategies: redact, replace (synthetic), token, hash
- **Zero runtime dependencies** — pure Python stdlib, Python 3.10+

## Install

```bash
pip install flexorch-audit
```

## Quick start

```python
from flexorch_audit import audit, mask

text = open("contract.txt").read()  # extract from PDF/DOCX first
result = audit(text, locale="tr")

result.quality_grade   # "A"
result.quality_score   # 0.91  (0.0–1.0 composite)
result.pii_summary     # [{"type": "national_id_tr", "count": 3}, {"type": "email", "count": 1}]

# Full findings and raw metrics — dict access also works:
result["pii"]          # [{"type": "email", "value": "...", "start": 8, "end": 23}]
result["quality"]      # {"completeness": 1.0, "avg_length": 342, "duplicate_ratio": None}
result["noise"]        # {"garbage_ratio": 0.0, "encoding_ok": True}

clean = mask(text, result["pii"], strategy="redact")
# "Contact: [REDACTED_EMAIL]"
```

![demo](assets/demo.svg)

## Batch audit

Use `audit_batch()` to audit an entire dataset and get aggregate metrics including `duplicate_ratio`:

```python
from flexorch_audit import audit_batch

texts = [record["text"] for record in dataset]
batch = audit_batch(texts, locale="tr")

batch["duplicate_ratio"]    # 0.12 — fraction of exact-duplicate records
batch["avg_quality_score"]  # 0.78
batch["pii_summary"]        # [{"type": "email", "count": 47}, ...]
batch["results"]            # list of AuditResult, one per text
```

## Locale support

| `locale` | Active detectors |
|----------|-----------------|
| `"tr"` (default) | email, iban, credit_card, ip, ip_v6 + TCKN, VKN, phone_tr, name |
| `"us"` | email, iban, credit_card, ip, ip_v6 + SSN, E.164 phone |
| `"eu"` | email, iban, credit_card, ip, ip_v6 + E.164 phone |
| `"all"` | All of the above (phone_tr takes precedence over generic phone) |

## PII types

| Type | Description | Locale |
|------|-------------|--------|
| `email` | RFC-5321 address | all |
| `iban` | ISO 13616 IBAN — mod-97 checksum validated | all |
| `credit_card` | 16-digit groups, Luhn-validated | all |
| `ip` | IPv4 address | all |
| `ip_v6` | IPv6 address (full, compressed, loopback) | all |
| `phone_tr` | Turkish mobile (+90/0 prefix + 10 digits) | tr |
| `national_id_tr` | TCKN — 11-digit modular arithmetic checksum | tr |
| `tax_id_tr` | VKN — 10-digit Luhn-variant checksum | tr |
| `name` | Label-prefixed name (e.g. "Adı: Ali Yıldız", "Full Name: Jane Doe") | tr |
| `phone` | E.164 international phone | us, eu |
| `ssn` | US Social Security Number (###-##-####) | us |

## Masking strategies

| Strategy | Example output |
|----------|----------------|
| `redact` (default) | `[REDACTED_EMAIL]` |
| `replace` | `user@example.com` (static synthetic) |
| `token` | `<PII_EMAIL_1>` (unique per type per call) |
| `hash` | `[3d4f9a1b2c8e7f0a]` (SHA-256 first 16 hex chars) |

## Quality grade

`quality_grade` (A–D) and `quality_score` (0.0–1.0) are composite signals:

| Grade | Score | Signal |
|-------|-------|--------|
| A | ≥ 0.85 | Ready for LLM training or RAG |
| B | ≥ 0.65 | Usable with minor cleanup |
| C | ≥ 0.40 | Review before use |
| D | < 0.40 | Not suitable — empty, too short, or high noise |

Score formula: `completeness × (0.4 × noise_score + 0.4 × length_score + 0.2)`  
`length_score = min(char_count / 500, 1.0)` · `noise_score = max(0, 1 − garbage_ratio × 10)`

## Limitations (v0.4)

- Free-standing name detection (without a label prefix) requires NLP/NER — not included.
- `replace` masking strategy uses static synthetic values; locale-aware realistic synthesis is not yet implemented.

## Also available for JavaScript / TypeScript

```bash
npm install @flexorch/audit
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
