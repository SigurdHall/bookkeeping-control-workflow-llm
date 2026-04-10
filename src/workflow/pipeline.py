from __future__ import annotations

import json
from pathlib import Path

from src.embeddings.similarity_search import find_similar_records
from src.etl.parse_invoice import parse_invoice_dict
from src.models.scoring import build_suggestion
from src.rules.rules_engine import evaluate_rules
from src.utils.schemas import HistoricalRecord, SuggestionResult


def load_historical_records(path: str | Path) -> list[HistoricalRecord]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [HistoricalRecord(**row) for row in data]


def run_pipeline(invoice_data: dict, historical_records: list[HistoricalRecord]) -> SuggestionResult:
    invoice = parse_invoice_dict(invoice_data)
    violations = evaluate_rules(invoice)
    matches = find_similar_records(invoice, historical_records, top_k=3)

    return build_suggestion(
        matches=matches,
        rule_violations=violations,
        fallback_cost_center=invoice.cost_center,
        fallback_project_code=invoice.project_code,
    )


if __name__ == "__main__":
    sample_invoice = {
        "invoice_id": "INV-001",
        "supplier_id": "SUP-100",
        "supplier_name": "Nordic Software AS",
        "description": "Annual software subscription for finance reporting",
        "amount": 8500.0,
        "currency": "NOK",
        "cost_center": "41010",
        "project_code": None,
        "vat_code": "25",
    }

    historical_path = Path("data/synthetic/historical_records.json")
    historical = load_historical_records(historical_path)
    result = run_pipeline(sample_invoice, historical)

    print(result.model_dump_json(indent=2))
