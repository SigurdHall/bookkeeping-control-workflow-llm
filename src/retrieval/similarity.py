from __future__ import annotations

from typing import Iterable, Protocol

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.schemas import HistoricalRecord, InvoiceRecord, SimilarMatch


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


def combine_transaction_text(supplier_name: str, description: str) -> str:
    return f"{supplier_name} {description}".strip().lower()


def find_similar_records_tfidf(
    invoice: InvoiceRecord,
    historical_records: Iterable[HistoricalRecord],
    top_k: int = 3,
) -> list[SimilarMatch]:
    records = list(historical_records)
    if not records:
        return []

    invoice_text = combine_transaction_text(invoice.supplier_name, invoice.description)
    historical_texts = [
        combine_transaction_text(record.supplier_name, record.description)
        for record in records
    ]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([invoice_text, *historical_texts])
    similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]

    ranked = sorted(
        zip(records, similarities, strict=False),
        key=lambda row: row[1],
        reverse=True,
    )[:top_k]

    return [_to_match(record, float(score)) for record, score in ranked]


def find_similar_records_with_embeddings(
    invoice: InvoiceRecord,
    historical_records: Iterable[HistoricalRecord],
    embedding_client: EmbeddingClient,
    top_k: int = 3,
) -> list[SimilarMatch]:
    records = list(historical_records)
    if not records:
        return []

    texts = [
        combine_transaction_text(invoice.supplier_name, invoice.description),
        *[
            combine_transaction_text(record.supplier_name, record.description)
            for record in records
        ],
    ]
    embeddings = embedding_client.embed_texts(texts)
    similarities = cosine_similarity([embeddings[0]], embeddings[1:])[0]

    ranked = sorted(
        zip(records, similarities, strict=False),
        key=lambda row: row[1],
        reverse=True,
    )[:top_k]
    return [_to_match(record, float(score)) for record, score in ranked]


def find_similar_records(
    invoice: InvoiceRecord,
    historical_records: Iterable[HistoricalRecord],
    top_k: int = 3,
    embedding_client: EmbeddingClient | None = None,
) -> list[SimilarMatch]:
    if embedding_client is None:
        return find_similar_records_tfidf(invoice, historical_records, top_k=top_k)
    return find_similar_records_with_embeddings(
        invoice=invoice,
        historical_records=historical_records,
        embedding_client=embedding_client,
        top_k=top_k,
    )


def _to_match(record: HistoricalRecord, score: float) -> SimilarMatch:
    return SimilarMatch(
        historical_id=record.historical_id,
        similarity_score=round(max(min(score, 1.0), 0.0), 4),
        account_code=record.account_code,
        supplier_name=record.supplier_name,
        description=record.description,
        amount=record.amount,
        cost_center=record.cost_center,
        project_code=record.project_code,
        vat_code=record.vat_code,
    )
