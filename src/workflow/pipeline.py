from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.config.settings import AppConfig, load_config
from src.etl.parse_invoice import parse_invoice_dict
from src.llm.clients import PostingLLMClient, build_llm_client
from src.llm.prompt_builder import build_posting_prompt
from src.models.scoring import build_suggestion
from src.retrieval.similarity import find_similar_records
from src.rules.rules_engine import evaluate_suggestion_rules
from src.utils.hashing import stable_model_hash
from src.utils.schemas import (
    HistoricalRecord,
    InvoiceRecord,
    PipelineCaseResult,
    RuleViolation,
    SimilarMatch,
    SuggestionResult,
)


def load_historical_records(path: str | Path) -> list[HistoricalRecord]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [HistoricalRecord(**row) for row in data]


def run_pipeline(
    invoice_data: dict,
    historical_records: list[HistoricalRecord],
    llm_client: PostingLLMClient | None = None,
    config: AppConfig | None = None,
) -> SuggestionResult:
    invoice = parse_invoice_dict(invoice_data)
    return run_invoice_pipeline(
        invoice=invoice,
        historical_records=historical_records,
        llm_client=llm_client,
        config=config,
    )


def run_invoice_pipeline(
    invoice: InvoiceRecord,
    historical_records: list[HistoricalRecord],
    llm_client: PostingLLMClient | None = None,
    config: AppConfig | None = None,
) -> SuggestionResult:
    config = config or load_config()
    llm_client = llm_client or build_llm_client(config.llm)

    matches = find_similar_records(
        invoice=invoice,
        historical_records=historical_records,
        top_k=config.retrieval.top_k,
    )
    prompt = build_posting_prompt(
        invoice=invoice,
        matches=matches,
        prompt_version=config.llm.prompt_version,
    )
    llm_suggestion = llm_client.suggest_posting(
        invoice=invoice,
        matches=matches,
        prompt=prompt,
        prompt_version=config.llm.prompt_version,
    )
    violations = evaluate_suggestion_rules(invoice, llm_suggestion)

    result = build_suggestion(
        matches=matches,
        rule_violations=violations,
        fallback_cost_center=invoice.cost_center,
        fallback_project_code=invoice.project_code,
        fallback_vat_code=invoice.vat_code,
        llm_suggestion=llm_suggestion,
        thresholds=config.thresholds,
    )
    result.metadata = {
        "prompt": prompt,
        "input_hash": stable_model_hash(invoice),
    }
    return result


def build_case_result(
    invoice: InvoiceRecord,
    result: SuggestionResult,
    run_id: str,
    processed_at: str | None = None,
) -> PipelineCaseResult:
    processed_at = processed_at or datetime.now(UTC).isoformat()
    llm = result.llm_suggestion
    return PipelineCaseResult(
        run_id=run_id,
        processed_at=processed_at,
        invoice_id=invoice.invoice_id,
        input_hash=stable_model_hash(invoice),
        decision=result.decision,
        confidence=result.confidence,
        suggested_account=result.suggested_account,
        suggested_cost_center=result.suggested_cost_center,
        suggested_project_code=result.suggested_project_code,
        suggested_vat_code=result.suggested_vat_code,
        status="needs_review" if result.decision in {"review", "stop"} else "suggested",
        reasons=result.reasons,
        prompt_version=llm.prompt_version if llm else "unknown",
        model_name=llm.model_name if llm else "unknown",
    )


def flatten_llm_suggestion(
    invoice: InvoiceRecord,
    result: SuggestionResult,
    run_id: str,
) -> dict:
    llm = result.llm_suggestion
    if llm is None:
        return {}
    return {
        "run_id": run_id,
        "invoice_id": invoice.invoice_id,
        **llm.model_dump(mode="json"),
    }


def flatten_retrieval_matches(
    invoice: InvoiceRecord,
    matches: list[SimilarMatch],
    run_id: str,
) -> list[dict]:
    return [
        {
            "run_id": run_id,
            "invoice_id": invoice.invoice_id,
            "rank": rank,
            **match.model_dump(mode="json"),
        }
        for rank, match in enumerate(matches, start=1)
    ]


def flatten_rule_violations(
    invoice: InvoiceRecord,
    violations: list[RuleViolation],
    run_id: str,
) -> list[dict]:
    return [
        {
            "run_id": run_id,
            "invoice_id": invoice.invoice_id,
            **violation.model_dump(mode="json"),
        }
        for violation in violations
    ]


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

    historical = load_historical_records("data/synthetic/historical_records.json")
    pipeline_result = run_pipeline(sample_invoice, historical)
    print(pipeline_result.model_dump_json(indent=2))
