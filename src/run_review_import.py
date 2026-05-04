from __future__ import annotations

import argparse
import logging

from src.config.settings import load_config
from src.review.review_io import append_decisions_to_historical_records, load_review_decisions
from src.utils.output_writer import write_dataset

logger = logging.getLogger(__name__)


def run_review_import(config_path: str = "config/default.yaml") -> int:
    config = load_config(config_path)
    decisions = load_review_decisions(config.paths.review_input_path)
    write_dataset(
        decisions,
        config.paths.output_dir,
        "review_decisions",
        config.outputs.write_csv,
        config.outputs.write_parquet,
    )

    review_queue_path = config.paths.review_dir / "review_queue.csv"
    if review_queue_path.exists():
        appended = append_decisions_to_historical_records(
            review_rows_path=review_queue_path,
            historical_path=config.paths.historical_path,
            decisions=decisions,
        )
        logger.info("Appended %s approved/corrected records to historical data.", len(appended))

    return len(decisions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import controller review decisions.")
    parser.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    count = run_review_import(args.config)
    logger.info("Imported %s review decisions.", count)


if __name__ == "__main__":
    main()
