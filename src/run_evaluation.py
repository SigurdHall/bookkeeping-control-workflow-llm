from __future__ import annotations

import argparse
import logging

import pandas as pd

from src.config.settings import load_config
from src.evaluation.metrics import build_evaluation_metrics
from src.utils.output_writer import write_dataset

logger = logging.getLogger(__name__)


def run_evaluation(config_path: str = "config/default.yaml") -> int:
    config = load_config(config_path)
    case_results_path = config.paths.output_dir / "case_results.csv"
    review_decisions_path = config.paths.output_dir / "review_decisions.csv"

    case_results = pd.read_csv(case_results_path)
    review_decisions = (
        pd.read_csv(review_decisions_path) if review_decisions_path.exists() else None
    )

    metrics = build_evaluation_metrics(case_results, review_decisions)
    write_dataset(
        metrics,
        config.paths.evaluation_output_dir,
        "evaluation_metrics",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )
    return len(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Power BI evaluation metrics.")
    parser.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    count = run_evaluation(args.config)
    logger.info("Wrote %s evaluation metrics.", count)


if __name__ == "__main__":
    main()
