# Changelog

All notable changes to flexorch-audit are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

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
- Limitations section updated with v0.4 targets

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

### [0.5.0] — Planned

- **Free-standing name detection** (NLP/NER): label-prefix not required; requires
  a lightweight multilingual NER model (xlm-roberta backbone, lazy-loaded)
- **Synthetic replacement strategy**: `mask(..., strategy="replace")` substitutes
  real synthetic values instead of `[MASKED_X]` tokens
  (e.g. random valid TCKN, plausible name, realistic phone)

### [0.6.0] — Planned

- **EU country-specific PII**: national IDs for DE/FR/IT/NL/ES/PL, VAT numbers,
  social insurance numbers
- **e-invoice formats**: UBL TR 1.2, Peppol BIS, EDIFACT basic field extraction
- **US PII expansion**: EIN (Employer ID), driver's license patterns, ZIP+4

### [0.7.0] — Planned

- **`flexorch-sdk`** (Python + TypeScript): REST client for the FlexOrch platform API,
  released once the API contract is stable post-pilot
- **Streaming / async API**: `audit_stream()` for large document processing
