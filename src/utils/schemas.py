from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class InvoiceRecord(BaseModel):
    invoice_id: str
    supplier_id: str | None = None
    supplier_name: str
    description: str
    amount: float
    currency: str = "NOK"
    cost_center: str | None = None
    project_code: str | None = None
    vat_code: str | None = None


class HistoricalRecord(BaseModel):
    historical_id: str
    supplier_name: str
    description: str
    amount: float
    account_code: str
    cost_center: str | None = None
    project_code: str | None = None


class RuleViolation(BaseModel):
    rule_id: str
    message: str
    severity: Literal["warning", "blocking"] = "warning"


class SimilarMatch(BaseModel):
    historical_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    account_code: str
    supplier_name: str
    description: str


class SuggestionResult(BaseModel):
    suggested_account: str | None
    suggested_cost_center: str | None = None
    suggested_project_code: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    decision: Literal["stop", "review", "suggest"]
    reasons: list[str]
    rule_violations: list[RuleViolation] = Field(default_factory=list)
    similar_matches: list[SimilarMatch] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
