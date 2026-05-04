from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Decision = Literal["stop", "review", "suggest"]
ReviewAction = Literal["approve", "correct", "reject"]


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

    @field_validator("supplier_name", "description")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class HistoricalRecord(BaseModel):
    historical_id: str
    supplier_name: str
    description: str
    amount: float
    account_code: str
    cost_center: str | None = None
    project_code: str | None = None
    vat_code: str | None = None


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
    amount: float | None = None
    cost_center: str | None = None
    project_code: str | None = None
    vat_code: str | None = None


class LLMSuggestion(BaseModel):
    suggested_account: str | None
    suggested_cost_center: str | None = None
    suggested_project_code: str | None = None
    suggested_vat_code: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    uncertainty_flags: list[str] = Field(default_factory=list)
    referenced_historical_ids: list[str] = Field(default_factory=list)
    prompt_version: str = "rag-posting-v1"
    model_name: str = "mock-llm"
    raw_response: dict[str, Any] = Field(default_factory=dict)


class SuggestionResult(BaseModel):
    suggested_account: str | None
    suggested_cost_center: str | None = None
    suggested_project_code: str | None = None
    suggested_vat_code: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    decision: Decision
    reasons: list[str]
    rule_violations: list[RuleViolation] = Field(default_factory=list)
    similar_matches: list[SimilarMatch] = Field(default_factory=list)
    llm_suggestion: LLMSuggestion | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineCaseResult(BaseModel):
    run_id: str
    processed_at: str
    invoice_id: str
    input_hash: str
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_account: str | None = None
    suggested_cost_center: str | None = None
    suggested_project_code: str | None = None
    suggested_vat_code: str | None = None
    status: str
    reasons: list[str] = Field(default_factory=list)
    prompt_version: str
    model_name: str


class ReviewQueueItem(BaseModel):
    run_id: str
    invoice_id: str
    supplier_name: str
    description: str
    amount: float
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_account: str | None = None
    suggested_cost_center: str | None = None
    suggested_project_code: str | None = None
    suggested_vat_code: str | None = None
    review_reason: str
    controller_action: ReviewAction | None = None
    corrected_account: str | None = None
    corrected_cost_center: str | None = None
    corrected_project_code: str | None = None
    corrected_vat_code: str | None = None
    reviewer: str | None = None
    reviewer_comment: str | None = None


class ReviewDecision(BaseModel):
    run_id: str
    invoice_id: str
    action: ReviewAction
    reviewer: str
    decided_at: str
    original_suggested_account: str | None = None
    final_account: str | None = None
    final_cost_center: str | None = None
    final_project_code: str | None = None
    final_vat_code: str | None = None
    reason: str | None = None


class EvaluationMetric(BaseModel):
    run_id: str
    metric_name: str
    metric_value: float
    metric_group: str = "overall"
