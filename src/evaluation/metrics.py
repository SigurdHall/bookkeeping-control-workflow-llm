from __future__ import annotations

from collections import Counter

import pandas as pd

from src.utils.schemas import EvaluationMetric


def build_evaluation_metrics(
    case_results: pd.DataFrame,
    review_decisions: pd.DataFrame | None = None,
) -> list[EvaluationMetric]:
    if case_results.empty:
        return []

    run_id = str(case_results["run_id"].iloc[0])
    total = float(len(case_results))
    metrics = [
        EvaluationMetric(run_id=run_id, metric_name="case_count", metric_value=total),
        EvaluationMetric(
            run_id=run_id,
            metric_name="average_confidence",
            metric_value=float(case_results["confidence"].mean()),
        ),
    ]

    decision_counts = Counter(case_results["decision"])
    for decision, count in decision_counts.items():
        metrics.append(
            EvaluationMetric(
                run_id=run_id,
                metric_name=f"{decision}_rate",
                metric_value=float(count) / total,
                metric_group="decision",
            )
        )

    if review_decisions is not None and not review_decisions.empty:
        reviewed_ids = set(review_decisions["invoice_id"])
        corrected = review_decisions[review_decisions["action"] == "correct"]
        metrics.extend(
            [
                EvaluationMetric(
                    run_id=run_id,
                    metric_name="review_completion_rate",
                    metric_value=len(reviewed_ids) / total,
                    metric_group="review",
                ),
                EvaluationMetric(
                    run_id=run_id,
                    metric_name="correction_rate",
                    metric_value=len(corrected) / total,
                    metric_group="review",
                ),
            ]
        )

    return metrics
