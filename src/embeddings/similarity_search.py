from __future__ import annotations

from typing import Iterable

from src.retrieval.similarity import find_similar_records as _find_similar_records
from src.utils.schemas import HistoricalRecord, InvoiceRecord, SimilarMatch


def find_similar_records(
    invoice: InvoiceRecord,
    historical_records: Iterable[HistoricalRecord],
    top_k: int = 3,
) -> list[SimilarMatch]:
    """Backward-compatible wrapper for the old module path."""
    return _find_similar_records(invoice, historical_records, top_k=top_k)
