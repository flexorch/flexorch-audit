import sys

from flexorch_audit import audit, mask

sys.stdout.reconfigure(encoding="utf-8")

TEXT = """\
Contract #1042  —  Employment Agreement

Full Name: Ali Yıldız
TC Kimlik: 12345678950
E-mail: ali.yildiz@flexorch.com
IBAN: TR330006100519786457841326

This agreement governs the employment relationship between
Flexorch Technology and the employee named above, including
confidentiality obligations and IP assignment clauses.
"""

result = audit(TEXT, locale="tr")

print()
print(f"  Grade  : {result.quality_grade}   (score: {result.quality_score})")
print(f"  PII    : {len(result.pii)} finding(s)")
for s in result.pii_summary:
    print(f"           {s['type']:<22} ×{s['count']}")
print()
print("  Masked output:")
clean = mask(TEXT, result["pii"], strategy="redact")
for line in clean.strip().splitlines():
    print(f"  {line}")
print()
