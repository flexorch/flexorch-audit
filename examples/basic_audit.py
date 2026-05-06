"""
Basic flexorch-audit usage — single document.

Run:
    python examples/basic_audit.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from flexorch_audit import audit, mask

SAMPLE_TEXT = """
Employment Agreement — Flexorch Technology

Employee: Adı Soyadı: Ali Yıldız
TC Kimlik No: 12345678950
E-posta: ali.yildiz@example.com
IBAN: TR330006100519786457841326

This agreement is entered into between Flexorch Technology and the above employee.
The terms outlined herein govern the employment relationship, including confidentiality,
intellectual property, and termination clauses. Both parties agree to comply with
applicable laws and regulations, including KVKK (Turkish Personal Data Protection Law).
"""

result = audit(SAMPLE_TEXT, locale="tr")

print(f"Quality grade : {result.quality_grade}")
print(f"Quality score : {result.quality_score}")
print(f"PII summary   : {result.pii_summary}")
print(f"Noise         : {result['noise']}")
print()

if result.pii_summary:
    print("Masked output:")
    clean = mask(SAMPLE_TEXT, result["pii"], strategy="redact")
    print(clean)
