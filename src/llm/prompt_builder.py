from __future__ import annotations

from src.utils.schemas import InvoiceRecord, SimilarMatch


def build_posting_prompt(
    invoice: InvoiceRecord,
    matches: list[SimilarMatch],
    prompt_version: str = "rag-posting-v1",
) -> str:
    examples = "\n".join(
        [
            (
                f"- historical_id={match.historical_id}; score={match.similarity_score}; "
                f"supplier={match.supplier_name}; description={match.description}; "
                f"account={match.account_code}; cost_center={match.cost_center}; "
                f"project={match.project_code}; vat={match.vat_code}"
            )
            for match in matches
        ]
    )
    if not examples:
        examples = "- No similar historical transactions were found."

    return f"""Prompt version: {prompt_version}
You are assisting a bookkeeping controller. Use the new transaction and the similar
historical transactions to propose a structured posting suggestion. Do not invent
policy. If context is weak, lower confidence and add uncertainty flags.

Return valid JSON with these keys:
suggested_account, suggested_cost_center, suggested_project_code, suggested_vat_code,
confidence, rationale, uncertainty_flags, referenced_historical_ids.

New transaction:
invoice_id={invoice.invoice_id}
supplier_id={invoice.supplier_id}
supplier_name={invoice.supplier_name}
description={invoice.description}
amount={invoice.amount}
currency={invoice.currency}
cost_center={invoice.cost_center}
project_code={invoice.project_code}
vat_code={invoice.vat_code}

Similar historical transactions:
{examples}
"""
