# Changelog

All notable changes to flexorch-audit are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.5.1] — 2026-05-14

### Fixed

- Import order in `demo/` and `examples/` scripts (E402 — `sys.stdout.reconfigure` moved after imports)
- Split `import sys, os, textwrap` in `demo/generate_svg.py` into separate lines (E401); removed unused `textwrap` import (F401)
- Duplicate `_valid_vkn` import in `tests/test_pii.py` (F811)
- Mid-file import block in `tests/test_pii.py` moved to module top (E402)
- Forward version reference (`v0.4 targets`) removed from v0.3.1 CHANGELOG entry

---

## [0.5.0] — 2026-05-13

### New fields in AuditResult

| Field | Type | Description |
|-------|------|-------------|
| `noise_ratio` | `float` | Fraction of lines that are blank or contain symbol noise (`[@#!~*=]{3+}`). Mirrors the FlexOrch pipeline quality-step threshold — values above 0.20 indicate a document likely to reduce extraction quality. |
| `detected_language` | `str` | The `locale` value passed to `audit()`. Reflects caller-controlled language selection; auto-detection is intentionally out of scope (zero-dependency constraint — see LIMITATIONS). |

### Changed defaults

`audit()`, `audit_batch()`, and `detect_pii()` now default to `locale="und"` (undetermined)
instead of `locale="tr"`. `"und"` activates **all** locale detectors — same as `"all"`,
which remains a valid alias.

**Why:** A global tool should scan for everything when the document language is unknown,
not silently ignore non-TR PII. Passing a specific locale is still recommended for
precision when the language is known.

**Migration:** If you relied on the `"tr"`-only default, add `locale="tr"` explicitly:
```python
result = audit(text, locale="tr")   # unchanged behaviour
result = audit(text)                # v0.5.0: now equivalent to locale="und"
```

### Tests

177 tests (was 131). All passing, 0 warnings.

---

## [0.4.0] — 2026-05-13

### New PII types

| Type | Locale | Description |
|------|--------|-------------|
| `iban_tr` | `tr` | Turkish IBAN (TR prefix, mod-97 validated) |
| `iban_intl` | `eu` | EU/GB/CH/NO IBAN — ISO 13616 country+length+mod-97 |
| `company_name_tr` | `tr` | Turkish company names with legal suffixes (A.Ş., Ltd.Şti., Koll.Şti., Koop., T.A.Ş.) |
| `mersis_no` | `tr` | 16-digit Turkish company registry (MERSIS) number |
| `postal_code_tr` | `tr` | Turkish postal codes — province plate 01–81 |
| `province_tr` | `tr` | All 81 Turkish provinces |
| `company_name_intl` | `eu`, `us` | International company names — GmbH, LLC, SAS, B.V., S.r.l., Inc., etc. |

### Improved detectors

- **`phone_intl`** (replaces `phone` in `eu`/`us` locales): upgraded to full E.164
  regex with digit-count validation (7–15 digits) and explicit TR (+90) exclusion.
  Type name changed from `phone` → `phone_intl`.

### IBAN deduplication

Locale-specific IBAN types (`iban_tr`, `iban_intl`) now take precedence over the
universal `iban` type when they cover the same span. The universal `iban` type
continues to fire for countries not covered by a locale-specific detector
(e.g. a German IBAN in `locale="tr"` still returns `iban`).

### Breaking changes

| Locale | Before | After |
|--------|--------|-------|
| `locale="tr"` | TR IBAN → `iban` | TR IBAN → `iban_tr` |
| `locale="eu"` | E.164 phone → `phone` | E.164 phone → `phone_intl` |
| `locale="eu"` | EU IBAN → `iban` | EU IBAN → `iban_intl` |
| `locale="us"` | E.164 phone → `phone` | E.164 phone → `phone_intl` |

**Migration:** Replace `f["type"] == "iban"` checks in `locale="tr"` with
`f["type"] in ("iban", "iban_tr")`. Replace `f["type"] == "phone"` in
`locale="eu"/"us"` with `f["type"] == "phone_intl"`.

### Tests

131 tests (was 97). All passing, 0 warnings.

---

## [0.3.1] — 2026-05-12

### New PII types

- **`tax_id_tr`** (VKN): 10-digit Luhn-variant Vergi Kimlik Numarası
- **`ip_v6`**: IPv6 — full 8-group, compressed `::`, loopback `::1` forms

### Improvements

- **IBAN**: ISO 7064 mod-97 checksum validation added — fake/random IBANs now rejected
- **`audit_batch()`** / **`auditBatch()`**: bulk text analysis with `duplicate_ratio`,
  `pii_summary`, `avg_quality_score`

### Other

- README rewritten: shields.io badges, "Why" section, locale table

---

## [0.2.0] — 2026-05-06

### New features

- `quality_grade` (A–D) + `quality_score` (0.0–1.0) + `pii_summary` added to `AuditResult`
- `AuditResult`: Python `dict` subclass + TypeScript interface
- `examples/`, `CONTRIBUTING.md`, CI workflow added

---

## [0.1.0] — 2026-05-01

Initial release.

- `audit(text, locale)` — PII + quality + noise in one call
- `mask(text, findings)` — redact / token / hash strategies
- Locales: `tr` (TCKN, phone_tr, name), `us` (SSN, phone), `eu` (phone)
- Universal: email, IBAN, credit card, IPv4

---

## Roadmap

### [0.6.0] — Planned

- **Free-standing name detection** (NLP/NER): label-prefix not required; requires
  a lightweight multilingual NER model (xlm-roberta backbone, lazy-loaded).
  Currently out of scope due to zero-dependency policy — will be an optional extra.
- **Synthetic replacement strategy**: `mask(..., strategy="replace")` substitutes
  real synthetic values instead of `[MASKED_X]` tokens
  (e.g. random valid TCKN, plausible name, realistic phone)

### [0.7.0] — Planned

- **`flexorch-sdk`** (Python + TypeScript): REST client for the FlexOrch platform API,
  released once the API contract is stable post-pilot
- **Streaming / async API**: `audit_stream()` for large document processing
