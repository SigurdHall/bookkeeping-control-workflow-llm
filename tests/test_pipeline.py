from src.utils.schemas import HistoricalRecord
from src.workflow.pipeline import run_pipeline


def test_pipeline_returns_valid_result():
    invoice_data = {
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

    historical_records = [
        HistoricalRecord(
            historical_id="H001",
            supplier_name="Nordic Software AS",
            description="Software subscription license",
            amount=4500.0,
            account_code="6790",
            cost_center="41010",
            project_code=None,
        ),
        HistoricalRecord(
            historical_id="H002",
            supplier_name="Cloud Reports AB",
            description="Reporting platform subscription",
            amount=4700.0,
            account_code="6790",
            cost_center="41010",
            project_code=None,
        ),
    ]

    result = run_pipeline(invoice_data, historical_records)

    assert result.decision in {"stop", "review", "suggest"}
    assert 0.0 <= result.confidence <= 1.0
