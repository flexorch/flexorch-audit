"""
LlamaIndex reader with PII audit and quality filtering.

Wraps flexorch-audit to audit each document before it enters your LlamaIndex
pipeline — adding quality grade, noise ratio, and PII summary as extra_info,
with an optional PII masking step.

Install:
    pip install flexorch-audit llama-index-core

Usage:
    from examples.llamaindex_reader import AuditedReader

    reader = AuditedReader()
    docs = reader.load_data(texts=["...", "..."])
    docs = reader.load_data(texts=[...], min_grade="B")   # skip C/D quality
    docs = reader.load_data(texts=[...], min_grade="A", mask_pii=True on reader)
"""

try:
    from llama_index.core import Document
    from llama_index.core.readers.base import BaseReader
except ImportError as exc:
    raise ImportError("llama-index-core required: pip install llama-index-core") from exc

from flexorch_audit import audit, mask


class AuditedReader(BaseReader):
    """
    LlamaIndex reader that audits texts with flexorch-audit before loading.

    Args:
        locale:    flexorch-audit locale ("und" = all detectors, "tr", "de", …)
        mask_pii:  If True, redact PII from document content before loading.
    """

    _GRADE_ORDER = {"A": 4, "B": 3, "C": 2, "D": 1}

    def __init__(self, locale: str = "und", mask_pii: bool = False) -> None:
        self.locale = locale
        self.mask_pii = mask_pii

    def load_data(  # type: ignore[override]
        self,
        texts: list[str],
        min_grade: str | None = None,
    ) -> list[Document]:
        """
        Audit and load a list of texts.

        Args:
            texts:      List of raw text strings.
            min_grade:  If set ("A", "B", "C"), skip documents below this quality grade.

        Returns:
            List of LlamaIndex Document objects with audit metadata in extra_info.
        """
        min_rank = self._GRADE_ORDER.get(min_grade or "D", 1)
        docs = []
        for text in texts:
            result = audit(text, locale=self.locale)
            if self._GRADE_ORDER[result.quality_grade] < min_rank:
                continue
            content = mask(text, result["pii"]) if self.mask_pii else text
            docs.append(Document(
                text=content,
                extra_info={
                    "quality_grade": result.quality_grade,
                    "quality_score": result.quality_score,
                    "noise_ratio": result.noise_ratio,
                    "pii_summary": result.pii_summary,
                    "pii_masked": self.mask_pii,
                },
            ))
        return docs


if __name__ == "__main__":
    SAMPLE_TEXTS = [
        "Invoice #1042\nBill to: ali.yildiz@example.com\nAmount: €1,250.00\nThis is a complete invoice.",
        "@@@ garbage line\n!!!\n---",  # low quality — will be filtered with min_grade="B"
        "Contract agreement between Flexorch Technology and the client. "
        "IBAN: TR330006100519786457841326. Terms apply.",
    ]

    reader = AuditedReader(locale="tr", mask_pii=True)
    docs = reader.load_data(SAMPLE_TEXTS, min_grade="B")
    for doc in docs:
        print(f"grade={doc.extra_info['quality_grade']}  pii={doc.extra_info['pii_summary']}")
        print(doc.text[:80])
        print()
