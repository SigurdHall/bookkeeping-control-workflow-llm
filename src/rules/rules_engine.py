from __future__ import annotations

from src.utils.schemas import InvoiceRecord, RuleViolation


def evaluate_rules(invoice: InvoiceRecord) -> list[RuleViolation]:
    """
    Very simple phase-1 rules engine.

    Rules:
    - Amount must be positive
    - Large invoices should have cost center
    - Certain keywords should require project code
    """
    violations: list[RuleViolation] = []

    if invoice.amount <= 0:
        violations.append(
            RuleViolation(
                rule_id="R001",
                message="Invoice amount must be greater than zero.",
                severity="blocking",
            )
        )

    if invoice.amount >= 10000 and not invoice.cost_center:
        violations.append(
            RuleViolation(
                rule_id="R002",
                message="Invoices above 10,000 NOK should include a cost center.",
                severity="warning",
            )
        )

    project_keywords = ["project", "implementation", "upgrade", "rollout"]
    if any(keyword in invoice.description.lower() for keyword in project_keywords):
        if not invoice.project_code:
            violations.append(
                RuleViolation(
                    rule_id="R003",
                    message="Project-related purchases should include a project code.",
                    severity="warning",
                )
            )

    return violations


def has_blocking_violations(violations: list[RuleViolation]) -> bool:
    return any(v.severity == "blocking" for v in violations)
