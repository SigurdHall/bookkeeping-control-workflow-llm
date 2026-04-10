from __future__ import annotations

import json
from pathlib import Path

from src.utils.schemas import InvoiceRecord


def parse_invoice_dict(data: dict) -> InvoiceRecord:
    """Validate and normalize a single invoice-like dictionary."""
    return InvoiceRecord(**data)


def load_invoice_json(path: str | Path) -> InvoiceRecord:
    """Load a single invoice JSON file."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return parse_invoice_dict(data)
