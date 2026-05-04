# Power BI Data Contract

All output datasets are written as CSV and Parquet when enabled in config.

## `case_results`

One row per processed invoice/voucher. Includes `run_id`, `processed_at`,
`invoice_id`, `input_hash`, `decision`, `confidence`, suggested posting fields,
`status`, `prompt_version`, and `model_name`.

## `llm_suggestions`

Structured LLM output. Includes suggested account/cost center/project/VAT,
confidence, rationale, uncertainty flags, referenced historical IDs, prompt
version, model name, and raw response where available.

## `retrieval_matches`

Top-k historical transactions used as prompt context. Includes rank, similarity
score, account, supplier, description, amount, cost center, project, and VAT.

## `rule_violations`

One row per deterministic control result. Includes rule ID, message, and
severity.

## `review_queue`

Cases requiring controller action. Controllers can add action fields:
`controller_action`, corrected posting fields, `reviewer`, and
`reviewer_comment`.

## `review_decisions`

Validated controller decisions. Human corrections never overwrite original LLM
suggestions.

## `evaluation_metrics`

Aggregated workflow metrics for Power BI reporting.
