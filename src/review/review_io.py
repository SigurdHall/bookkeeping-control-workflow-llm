from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pandas as pd

from src.utils.schemas import (
    Decision,
    HistoricalRecord,
    ReviewAction,
    ReviewDecision,
    ReviewQueueItem,
)


def _text_or_none(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def build_review_queue_item(
    invoice_id: str,
    supplier_name: str,
    description: str,
    amount: float,
    run_id: str,
    decision: Decision,
    confidence: float,
    suggested_account: str | None,
    suggested_cost_center: str | None,
    suggested_project_code: str | None,
    suggested_vat_code: str | None,
    review_reason: str,
) -> ReviewQueueItem:
    return ReviewQueueItem(
        run_id=run_id,
        invoice_id=invoice_id,
        supplier_name=supplier_name,
        description=description,
        amount=amount,
        decision=decision,
        confidence=confidence,
        suggested_account=suggested_account,
        suggested_cost_center=suggested_cost_center,
        suggested_project_code=suggested_project_code,
        suggested_vat_code=suggested_vat_code,
        review_reason=review_reason,
    )


def load_review_decisions(path: str | Path) -> list[ReviewDecision]:
    path = Path(path)
    frame = pd.read_excel(path) if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(path)
    rows = frame.astype(object).where(pd.notnull(frame), None).to_dict(orient="records")
    decided_at = datetime.now(UTC).isoformat()

    decisions: list[ReviewDecision] = []
    for row in rows:
        action_value = (_text_or_none(row.get("controller_action")) or _text_or_none(row.get("action")) or "").lower()
        reviewer = _text_or_none(row.get("reviewer"))
        if action_value not in {"approve", "correct", "reject"} or not reviewer:
            raise ValueError("Review rows must include controller_action/action and reviewer.")
        action = cast(ReviewAction, action_value)

        original_account = _text_or_none(row.get("suggested_account")) or _text_or_none(
            row.get("original_suggested_account")
        )
        final_account = _text_or_none(row.get("corrected_account")) or original_account
        if action == "reject":
            final_account = None

        decisions.append(
            ReviewDecision(
                run_id=str(row["run_id"]),
                invoice_id=str(row["invoice_id"]),
                action=action,
                reviewer=reviewer,
                decided_at=decided_at,
                original_suggested_account=original_account,
                final_account=final_account,
                final_cost_center=_text_or_none(row.get("corrected_cost_center"))
                or _text_or_none(row.get("suggested_cost_center")),
                final_project_code=_text_or_none(row.get("corrected_project_code"))
                or _text_or_none(row.get("suggested_project_code")),
                final_vat_code=_text_or_none(row.get("corrected_vat_code"))
                or _text_or_none(row.get("suggested_vat_code")),
                reason=_text_or_none(row.get("reviewer_comment")) or _text_or_none(row.get("reason")),
            )
        )
    return decisions


def append_decisions_to_historical_records(
    review_rows_path: str | Path,
    historical_path: str | Path,
    decisions: list[ReviewDecision],
) -> list[HistoricalRecord]:
    review_frame = pd.read_csv(review_rows_path)
    review_rows = {
        str(row["invoice_id"]): row
        for row in review_frame.astype(object).where(pd.notnull(review_frame), None).to_dict(orient="records")
    }

    historical_path = Path(historical_path)
    with historical_path.open("r", encoding="utf-8") as file:
        historical_data = json.load(file)

    new_records: list[HistoricalRecord] = []
    for decision in decisions:
        if decision.action == "reject" or not decision.final_account:
            continue
        source = review_rows.get(decision.invoice_id)
        if not source:
            continue
        new_records.append(
            HistoricalRecord(
                historical_id=f"REV-{decision.run_id}-{decision.invoice_id}",
                supplier_name=str(source["supplier_name"]),
                description=str(source["description"]),
                amount=float(source["amount"]),
                account_code=decision.final_account,
                cost_center=decision.final_cost_center,
                project_code=decision.final_project_code,
                vat_code=decision.final_vat_code,
            )
        )

    existing_ids = {row["historical_id"] for row in historical_data}
    for record in new_records:
        if record.historical_id not in existing_ids:
            historical_data.append(record.model_dump(mode="json"))

    with historical_path.open("w", encoding="utf-8") as file:
        json.dump(historical_data, file, indent=2, ensure_ascii=False)
        file.write("\n")

    return new_records
