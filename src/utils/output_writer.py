from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel


def models_to_frame(records: list[BaseModel]) -> pd.DataFrame:
    return pd.DataFrame([record.model_dump(mode="json") for record in records])


def dicts_to_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records)


def write_dataset(
    records: list[BaseModel] | list[dict[str, Any]],
    output_dir: str | Path,
    dataset_name: str,
    write_csv: bool = True,
    write_parquet: bool = True,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not records:
        frame = pd.DataFrame()
    elif isinstance(records[0], BaseModel):
        frame = models_to_frame(records)  # type: ignore[arg-type]
    else:
        frame = dicts_to_frame(records)  # type: ignore[arg-type]

    if write_csv:
        frame.to_csv(output_path / f"{dataset_name}.csv", index=False)
    if write_parquet:
        frame.to_parquet(output_path / f"{dataset_name}.parquet", index=False)
