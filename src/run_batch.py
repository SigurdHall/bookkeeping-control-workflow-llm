from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime

from src.config.settings import load_config
from src.etl.parse_invoice import load_invoice_table
from src.llm.clients import build_llm_client
from src.review.review_io import build_review_queue_item
from src.utils.output_writer import write_dataset
from src.workflow.pipeline import (
    build_case_result,
    flatten_llm_suggestion,
    flatten_retrieval_matches,
    flatten_rule_violations,
    load_historical_records,
    run_invoice_pipeline,
)

logger = logging.getLogger(__name__)


def run_batch(config_path: str = "config/default.yaml") -> str:
    config = load_config(config_path)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    processed_at = datetime.now(UTC).isoformat()

    invoices = load_invoice_table(config.paths.input_path)
    historical = load_historical_records(config.paths.historical_path)
    llm_client = build_llm_client(config.llm)

    case_results = []
    llm_suggestions = []
    retrieval_matches = []
    rule_violations = []
    review_queue = []

    for invoice in invoices:
        result = run_invoice_pipeline(
            invoice=invoice,
            historical_records=historical,
            llm_client=llm_client,
            config=config,
        )
        case_results.append(build_case_result(invoice, result, run_id, processed_at))
        llm_suggestions.append(flatten_llm_suggestion(invoice, result, run_id))
        retrieval_matches.extend(flatten_retrieval_matches(invoice, result.similar_matches, run_id))
        rule_violations.extend(flatten_rule_violations(invoice, result.rule_violations, run_id))

        if result.decision in {"review", "stop"}:
            review_queue.append(
                build_review_queue_item(
                    invoice_id=invoice.invoice_id,
                    supplier_name=invoice.supplier_name,
                    description=invoice.description,
                    amount=invoice.amount,
                    run_id=run_id,
                    decision=result.decision,
                    confidence=result.confidence,
                    suggested_account=result.suggested_account,
                    suggested_cost_center=result.suggested_cost_center,
                    suggested_project_code=result.suggested_project_code,
                    suggested_vat_code=result.suggested_vat_code,
                    review_reason="; ".join(result.reasons),
                )
            )

    write_dataset(
        case_results,
        config.paths.output_dir,
        "case_results",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )
    write_dataset(
        [row for row in llm_suggestions if row],
        config.paths.output_dir,
        "llm_suggestions",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )
    write_dataset(
        retrieval_matches,
        config.paths.output_dir,
        "retrieval_matches",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )
    write_dataset(
        rule_violations,
        config.paths.output_dir,
        "rule_violations",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )
    write_dataset(
        review_queue,
        config.paths.review_dir,
        "review_queue",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )

    logger.info("Processed %s invoices for run_id=%s", len(invoices), run_id)
    return run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM-first bookkeeping control batch.")
    parser.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_batch(args.config)


if __name__ == "__main__":
    main()
