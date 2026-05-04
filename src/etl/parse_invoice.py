from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.utils.schemas import InvoiceRecord

OPTIONAL_TEXT_FIELDS = {"supplier_id", "cost_center", "project_code", "vat_code"}


def _normalize_invoice_values(data: dict) -> dict:
    normalized = dict(data)
    for field in OPTIONAL_TEXT_FIELDS:
        value = normalized.get(field)
        if value is None or pd.isna(value):
            normalized[field] = None
        else:
            normalized[field] = str(value)
    return normalized


def parse_invoice_dict(data: dict) -> InvoiceRecord:
    """Validate and normalize a single invoice-like dictionary."""
    return InvoiceRecord(**_normalize_invoice_values(data))


def load_invoice_json(path: str | Path) -> InvoiceRecord:
    """Load a single invoice JSON file."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return parse_invoice_dict(data)


def load_invoice_table(path: str | Path) -> list[InvoiceRecord]:
    """Load invoice-like records from CSV or Excel."""
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    else:
        frame = pd.read_csv(path)

    records: list[InvoiceRecord] = []
    for row in frame.astype(object).where(pd.notnull(frame), None).to_dict(orient="records"):
        records.append(parse_invoice_dict(row))
    return records
