from __future__ import annotations

from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.schemas import HistoricalRecord, InvoiceRecord, SimilarMatch


def _combine_text(supplier_name: str, description: str) -> str:
    return f"{supplier_name} {description}".strip().lower()


def find_similar_records(
    invoice: InvoiceRecord,
    historical_records: Iterable[HistoricalRecord],
    top_k: int = 3,
) -> list[SimilarMatch]:
    historical_records = list(historical_records)
    if not historical_records:
        return []

    invoice_text = _combine_text(invoice.supplier_name, invoice.description)
    historical_texts = [
        _combine_text(record.supplier_name, record.description)
        for record in historical_records
    ]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([invoice_text, *historical_texts])

    invoice_vector = matrix[0:1]
    historical_matrix = matrix[1:]

    similarities = cosine_similarity(invoice_vector, historical_matrix)[0]

    ranked = sorted(
        zip(historical_records, similarities, strict=False),
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]

    results: list[SimilarMatch] = []
    for record, score in ranked:
        results.append(
            SimilarMatch(
                historical_id=record.historical_id,
                similarity_score=float(score),
                account_code=record.account_code,
                supplier_name=record.supplier_name,
                description=record.description,
            )
        )

    return results
