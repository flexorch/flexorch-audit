"""
LangChain document loader with PII audit and quality filtering.

Wraps flexorch-audit to audit each document before it enters your LangChain
pipeline — adding quality grade, noise ratio, and PII summary as metadata,
with an optional PII masking step.

Install:
    pip install flexorch-audit langchain-core

Usage:
    from examples.langchain_loader import AuditedLoader

    loader = AuditedLoader(texts=["...", "..."])
    docs = loader.load()                       # all documents
    docs = loader.load()                       # AuditedLoader.load() uses lazy_load()
    loader2 = AuditedLoader(texts=[...], min_grade="B", mask_pii=True)
    docs = loader2.load()                      # skip D/C quality, PII redacted
"""

try:
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.documents import Document
except ImportError as exc:
    raise ImportError("langchain-core required: pip install langchain-core") from exc

from typing import Iterator

from flexorch_audit import audit, mask


class AuditedLoader(BaseLoader):
    """
    LangChain loader that audits texts with flexorch-audit before loading.

    Args:
        texts:      List of raw text strings to load.
        locale:     flexorch-audit locale ("und" = all detectors, "tr", "de", …)
        mask_pii:   If True, redact PII from document content before loading.
        min_grade:  If set ("A", "B", "C"), skip documents below this quality grade.
    """

    _GRADE_ORDER = {"A": 4, "B": 3, "C": 2, "D": 1}

    def __init__(
        self,
        texts: list[str],
        locale: str = "und",
        mask_pii: bool = False,
        min_grade: str | None = None,
    ) -> None:
        self.texts = texts
        self.locale = locale
        self.mask_pii = mask_pii
        self.min_grade = min_grade

    def lazy_load(self) -> Iterator[Document]:
        min_rank = self._GRADE_ORDER.get(self.min_grade or "D", 1)
        for text in self.texts:
            result = audit(text, locale=self.locale)
            if self._GRADE_ORDER[result.quality_grade] < min_rank:
                continue
            content = mask(text, result["pii"]) if self.mask_pii else text
            yield Document(
                page_content=content,
                metadata={
                    "quality_grade": result.quality_grade,
                    "quality_score": result.quality_score,
                    "noise_ratio": result.noise_ratio,
                    "pii_summary": result.pii_summary,
                    "pii_masked": self.mask_pii,
                },
            )


if __name__ == "__main__":
    SAMPLE_TEXTS = [
        "Invoice #1042\nBill to: ali.yildiz@example.com\nAmount: €1,250.00\nThis is a complete invoice.",
        "@@@ garbage line\n!!!\n---",  # low quality — will be filtered with min_grade="B"
        "Contract agreement between Flexorch Technology and the client. "
        "IBAN: TR330006100519786457841326. Terms apply.",
    ]

    loader = AuditedLoader(SAMPLE_TEXTS, locale="tr", mask_pii=True, min_grade="B")
    for doc in loader.lazy_load():
        print(f"grade={doc.metadata['quality_grade']}  pii={doc.metadata['pii_summary']}")
        print(doc.page_content[:80])
        print()
