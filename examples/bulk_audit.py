"""
Bulk dataset audit — compute aggregate quality stats and duplicate ratio.

Useful when you have a list of extracted text records (e.g., from a CSV or JSONL file)
and want to triage them before loading into a fine-tuning or RAG pipeline.

Run:
    python examples/bulk_audit.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from flexorch_audit import audit

RECORDS = [
    "The transformer architecture introduced self-attention, enabling parallel processing "
    "of sequences and significantly improving performance on NLP tasks.",
    "IBAN: TR330006100519786457841326 — please transfer funds by Friday.",
    "   ",  # empty / whitespace only
    "The transformer architecture introduced self-attention, enabling parallel processing "
    "of sequences and significantly improving performance on NLP tasks.",  # duplicate
    "Retrieval-augmented generation (RAG) combines a retrieval component with a generative "
    "model, allowing the system to ground responses in external knowledge bases.",
]

results = [audit(r, locale="tr") for r in RECORDS]

# Duplicate ratio across the dataset
seen: set[str] = set()
duplicates = 0
for r in RECORDS:
    if r.strip() in seen:
        duplicates += 1
    else:
        seen.add(r.strip())
duplicate_ratio = round(duplicates / len(RECORDS), 4)

print(f"{'#':<4} {'Grade':<7} {'Score':<8} {'PII':<5} Record preview")
print("-" * 65)
for i, (record, result) in enumerate(zip(RECORDS, results)):
    preview = record.strip()[:40].replace("\n", " ") or "(empty)"
    n_pii = len(result["pii"])
    print(f"{i:<4} {result.quality_grade:<7} {result.quality_score:<8} {n_pii:<5} {preview}")

print()
print(f"Duplicate ratio (dataset-level): {duplicate_ratio}")
grades = [r.quality_grade for r in results]
for g in ("A", "B", "C", "D"):
    print(f"  Grade {g}: {grades.count(g)} record(s)")
