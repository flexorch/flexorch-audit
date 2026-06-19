# Changelog

All notable changes to flexorch-audit are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.9.0] — 2026-06-19

### Added

**New Turkish social security PII detectors (G5.1 — SGK deepening)**

| Detector | Locale | Field | Algorithm |
|----------|--------|-------|-----------|
| `emeklilik_no` | `tr` | Emeklilik Sicil Numarası (retirement ID) | Label-prefix (`Emeklilik No:`, `Emekli Sicil No:`, `Emekli Maaşı No:`, `E Sicil:`) + 9–11 digit capture |
| `isyeri_sicil_no` | `tr` | İşyeri SGK Sicil Numarası (employer ID) | Label-prefix (`İşyeri SGK Kodu:`, `İşyeri Tescil No:`, `SGK İşyeri Kodu:`) + 8–9 digit capture |
| `bagkur_no` | `tr` | Bağ-Kur Sicil Numarası (self-employed ID) | Label-prefix (`Bağ-Kur Sicil No:`, `4/b Sicil No:`, `Kendi Namına Çalışan SGK No:`) + 10–11 digit capture |

All three detectors are active in `tr` and `und`/`all` locales.
Payroll dataset extraction schema updated: `sgk_isyeri_kodu`, `emeklilik_no`, `bagkur_no` fields added.

### Fixed

- **Stale redact assertion in `tests/test_api.py`**: `test_mask_redact_round_trip` was asserting `[REDACTED_EMAIL]` but v0.8.2 changed the redact placeholder to `[MASKED_EMAIL]`. Assertion updated to match current behavior.

---

## [0.8.2] — 2026-06-18

### Fixed

- **Masking prefix alignment**: `strategy="redact"` now produces `[MASKED_EMAIL]` / `[MASKED_NATIONAL_ID_TR]` etc., matching the FlexOrch platform API output. Previous prefix `[REDACTED_...]` diverged from the core platform, causing inconsistent placeholders when both were used in the same pipeline.

---

## [0.8.1] — 2026-06-12

### Added

**New PII detectors (TR SGK + EU PL/PT/SE/DK/FI)**

| Detector | Locale | Field | Algorithm |
|----------|--------|-------|-----------|
| `sgk_no` | `tr` | SGK Sicil Numarası | Label-prefix (`SGK No:`, `SSK No:`, `Sigortalı No:`) |
| `tax_id_pl` | `pl` | NIP (Numer Identyfikacji Podatkowej) | Label-prefix (`NIP:`) |
| `tax_id_pt` | `pt` | NIF (Número de Identificação Fiscal) | Label-prefix + weighted mod-11 checksum |
| `national_id_se` | `sv` | Personnummer | Format `YYMMDD[-+]\d{4}` or `YYYYMMDD-\d{4}` |
| `national_id_dk` | `da` | CPR (Civil Personal Register) | Format `DDMMYY-XXXX` |
| `national_id_fi` | `fi` | HETU (Henkilötunnus) | Format `DDMMYY[+\-A]\d{3}[checksum]` |

**Locale gate fixes**

- `de` locale now includes `social_id_at` — Austrian documents in German trigger AT SVNr detection (matches JS package behaviour)
- `fr` locale now includes `national_id_be` — Belgium is bilingual; French-language BE docs detect Belgian RRN
- `nl` locale now includes `national_id_be` — same rationale for Dutch-language BE docs

**New locales registered**

- `pt` (Portuguese), `sv` (Swedish), `da` (Danish), `fi` (Finnish) added to `_LOCALE_DETECTORS`

**Tests**

- 25 new tests — `tests/test_pii.py` (243 total)

---

## [0.7.0] — 2026-06-11

### Added

- **`redact_for_llm(text, locale, strategy)`** — one-shot audit + mask convenience wrapper; returns PII-free text ready for LLM processing in a single call
- **`estimate_tokens(text)`** — word-based token count heuristic (words × 4/3); no tiktoken dependency; accuracy ~15% for planning/cost estimates
- **LangChain integration** — `examples/langchain_loader.py`: `AuditedLoader(BaseLoader)` with `min_grade` quality filter and optional PII masking; audit metadata exposed in `doc.metadata`
- **LlamaIndex integration** — `examples/llamaindex_reader.py`: `AuditedReader(BaseReader)` with same filter/masking API; audit metadata in `doc.extra_info`
- README: "One-shot redaction", "Token estimation", "Integrations" sections with LangChain + LlamaIndex badges

---

## [0.6.0] — 2026-05-24

### Added

**New PII detectors (EU locales)**

| Detector | Locale | Field | Algorithm |
|----------|--------|-------|-----------|
| `national_id_pl` | `pl` | PESEL | 10-weight checksum, weights `[1,3,7,9,1,3,7,9,1,3]` |
| `social_id_at`   | `at` | Sozialversicherungsnummer | Luhn-style, 10 weights, check at position 3 |
| `national_id_be` | `be` | Rijksregisternummer/NISS | mod-97, pre- and post-2000 birth year branches |

All three are also active in the `und`/`all` locale.

**`audit_stream()` — async generator API**

```python
async for result in audit_stream(lines()):
    print(result.quality_grade, result.pii_summary)
```

Audits texts one at a time from any `AsyncIterable[str]`.  
Each text is processed via `asyncio.to_thread()` so the event loop is not blocked.

**`compliance_report()` — KVKK/GDPR risk summary**

```python
report = compliance_report(audit(text))
report["risk_level"]       # "none" | "low" | "medium" | "high"
report["masking_required"] # True when any PII was found
report["recommendations"]  # actionable next steps
```

Risk classification:
- **high** — national IDs, SSN, credit card, tax IDs
- **medium** — email, phone, IBAN, name
- **low** — company names and other lower-risk types
- **none** — no PII detected

**`mask(strategy="replace")` — deterministic synthetic values**

`replace` now produces checksum-valid synthetic replacements:

| PII type | Synthetic value |
|----------|----------------|
| `national_id_tr` | valid TCKN (checksum verified) |
| `iban_tr` / `iban_intl` | valid TR IBAN (mod-97 verified) |
| `name` | Turkish name from pool |
| `email`, `phone_tr`, `ssn`, `ip`, `ip_v6`, … | static safe values |

Replacement is deterministic: same original value always maps to the same synthetic replacement (SHA-256 seed).

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
