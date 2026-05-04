import json
from pathlib import Path

import pandas as pd

from src.config.settings import AppConfig
from src.llm.prompt_builder import build_posting_prompt
from src.retrieval.similarity import find_similar_records
from src.run_batch import run_batch
from src.run_evaluation import run_evaluation
from src.run_review_import import run_review_import
from src.utils.schemas import HistoricalRecord, InvoiceRecord
from src.workflow.pipeline import run_pipeline


def _invoice_data() -> dict:
    return {
        "invoice_id": "INV-TEST-001",
        "supplier_id": "SUP-100",
        "supplier_name": "Nordic Software AS",
        "description": "Software subscription for budgeting and reporting",
        "amount": 5000.0,
        "currency": "NOK",
        "cost_center": "41010",
        "project_code": None,
        "vat_code": "25",
    }


def _historical_records() -> list[HistoricalRecord]:
    return [
        HistoricalRecord(
            historical_id="H001",
            supplier_name="Nordic Software AS",
            description="Software subscription license",
            amount=4500.0,
            account_code="6790",
            cost_center="41010",
            project_code=None,
            vat_code="25",
        ),
        HistoricalRecord(
            historical_id="H002",
            supplier_name="Office Supplies Norge",
            description="Office materials",
            amount=700.0,
            account_code="6800",
            cost_center="42020",
            project_code=None,
            vat_code="25",
        ),
    ]


def test_retrieval_returns_top_k_match():
    invoice = InvoiceRecord(**_invoice_data())

    matches = find_similar_records(invoice, _historical_records(), top_k=1)

    assert len(matches) == 1
    assert matches[0].historical_id == "H001"
    assert matches[0].account_code == "6790"


def test_prompt_contains_invoice_and_retrieved_examples():
    invoice = InvoiceRecord(**_invoice_data())
    matches = find_similar_records(invoice, _historical_records(), top_k=1)

    prompt = build_posting_prompt(invoice, matches)

    assert "INV-TEST-001" in prompt
    assert "H001" in prompt
    assert "Return valid JSON" in prompt


def test_pipeline_returns_llm_first_result():
    result = run_pipeline(_invoice_data(), _historical_records(), config=AppConfig())

    assert result.llm_suggestion is not None
    assert result.suggested_account == "6790"
    assert result.decision in {"stop", "review", "suggest"}
    assert 0.0 <= result.confidence <= 1.0


def test_batch_review_and_evaluation_outputs(tmp_path: Path):
    input_path = tmp_path / "invoices.csv"
    historical_path = tmp_path / "historical_records.json"
    output_dir = tmp_path / "output"
    review_dir = tmp_path / "review"
    config_path = tmp_path / "config.yaml"

    pd.DataFrame([_invoice_data()]).to_csv(input_path, index=False)
    historical_path.write_text(
        json.dumps([record.model_dump(mode="json") for record in _historical_records()]),
        encoding="utf-8",
    )
    config_path.write_text(
        f"""
paths:
  input_path: {input_path.as_posix()}
  historical_path: {historical_path.as_posix()}
  output_dir: {output_dir.as_posix()}
  review_dir: {review_dir.as_posix()}
  review_input_path: {(review_dir / "review_decisions.csv").as_posix()}
  evaluation_output_dir: {output_dir.as_posix()}
outputs:
  write_csv: true
  write_parquet: false
""",
        encoding="utf-8",
    )

    run_id = run_batch(str(config_path))

    assert run_id
    assert (output_dir / "case_results.csv").exists()
    assert (output_dir / "llm_suggestions.csv").exists()
    assert (output_dir / "retrieval_matches.csv").exists()

    review_queue = pd.read_csv(review_dir / "review_queue.csv")
    if review_queue.empty:
        review_queue = pd.DataFrame(
            [
                {
                    "run_id": run_id,
                    "invoice_id": "INV-TEST-001",
                    "supplier_name": "Nordic Software AS",
                    "description": "Software subscription for budgeting and reporting",
                    "amount": 5000.0,
                    "suggested_account": "6790",
                    "suggested_cost_center": "41010",
                    "suggested_project_code": None,
                    "suggested_vat_code": "25",
                    "controller_action": "approve",
                    "reviewer": "controller@example.com",
                }
            ]
        )
        review_queue.to_csv(review_dir / "review_queue.csv", index=False)
    else:
        review_queue["controller_action"] = "approve"
        review_queue["reviewer"] = "controller@example.com"

    review_queue.to_csv(review_dir / "review_decisions.csv", index=False)
    imported = run_review_import(str(config_path))

    assert imported >= 1
    assert (output_dir / "review_decisions.csv").exists()

    metric_count = run_evaluation(str(config_path))

    assert metric_count >= 2
    assert (output_dir / "evaluation_metrics.csv").exists()
