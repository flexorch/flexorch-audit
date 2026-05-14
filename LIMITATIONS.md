# Limitations

flexorch-audit is a **zero-dependency** static analysis library. The following capabilities
are intentionally out of scope to preserve that constraint. They exist in the FlexOrch
platform (closed-source) but not in this package.

---

## Automatic language detection

`audit()` does **not** detect the document language automatically. The `locale` parameter
must be supplied by the caller. When the language is unknown, pass `locale="und"` (the
default) to activate all detectors.

**Why:** Auto-detection requires a statistical language model (e.g. langdetect, fastText).
Adding it would violate the zero-dependency policy.

**Workaround:** Use any language detection library of your choice and pass the result:
```python
from langdetect import detect          # your own dependency
locale = detect(text)[:2].lower()      # "tr", "de", "fr", etc.
result = audit(text, locale=locale)
```

---

## Free-standing name detection (NLP/NER)

`name` detection only fires when preceded by a recognised label prefix
(`Adı:`, `Full Name:`, `Customer Name:`, etc.). Bare names in running text
(e.g. `"Ali Yılmaz signed the contract"`) are not detected.

**Why:** Free-standing NER requires a multilingual model (xlm-roberta backbone).
Planned as an optional extra in a future release.

---

## Document pipeline and extraction

flexorch-audit audits **plain text**. It does not:

- Parse PDF, DOCX, HTML, XML, or any binary format
- Extract structured fields (invoice number, line items, totals)
- Route documents by type or apply industry-specific rule sets
- Run quality scoring on tabular / structured data (only unstructured text)

These are provided by the FlexOrch platform pipeline.

---

## e-Invoice / UBL parsing

The package does not parse UBL TR 1.2, Peppol BIS, GİB XML, EDIFACT, or any
e-invoice format. It can run PII detection on text extracted from such documents,
but the extraction itself is out of scope.

---

## Webhooks and event delivery

No webhook dispatch, HMAC signing, or event notification. These are platform-level
features not applicable to a text-analysis library.

---

## Persistent storage and dataset management

No database, file I/O, or dataset export. The library operates entirely in memory
on the text passed to `audit()`.

---

## Rate limiting and quota enforcement

No rate limits, credit tracking, or plan-based restrictions. All functions are
synchronous and stateless.

---

## Accuracy and false positives

Regex-based detectors optimise for recall over precision. Expect some false positives,
especially for:

- Short numeric sequences (BSN NL, Partita IVA IT) in dense numeric text
- Company name patterns in capitalized headings
- Phone numbers in IP addresses or reference codes

Apply locale narrowing (`locale="tr"` instead of `locale="und"`) and post-filter
by document context to reduce noise in production use.
