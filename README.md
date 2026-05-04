# Bookkeeping Control Workflow with LLM-first RAG

Prototype for an auditable bookkeeping control workflow where an LLM proposes
structured posting suggestions from top-k similar historical transactions, rules
validate the suggestion, and a human controller approves, corrects, or rejects.

This is not a fully automated posting engine. It is an implementation-oriented
MVP for testing a controlled workflow before production integration.

## Architecture

```text
ERP CSV/Excel export
  -> input validation
  -> top-k similar historical transactions
  -> LLM structured suggestion
  -> deterministic rule validation
  -> route to suggest / review / stop
  -> Power BI datasets
  -> human controller review
  -> approved/corrected cases appended to retrieval history
```

The default LLM provider is `mock`, so tests and local runs do not call external
services. Azure OpenAI is available behind the same client interface and should
only be enabled after privacy, access, retention, and logging controls are
approved for the relevant data.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional Azure OpenAI settings are documented in `.env.example`.

## Run Locally

The default config uses synthetic data and the mock LLM:

```powershell
python -m src.run_batch --config config/default.yaml
python -m src.run_review_import --config config/default.yaml
python -m src.run_evaluation --config config/default.yaml
```

Outputs are written to `data/output` and `data/review` as CSV and Parquet.

## Main Files

- `src/run_batch.py` runs the full LLM-first RAG batch.
- `src/run_review_import.py` imports controller decisions and appends approved
  or corrected cases to the historical retrieval set.
- `src/run_evaluation.py` writes Power BI-ready evaluation metrics.
- `src/llm` contains prompt construction, mock LLM, and Azure OpenAI client.
- `src/retrieval` contains top-k retrieval with TF-IDF fallback.
- `src/rules` contains deterministic controls that validate the LLM suggestion.

## Power BI Outputs

- `case_results`: one row per invoice/voucher.
- `llm_suggestions`: structured LLM output and rationale.
- `retrieval_matches`: top-k historical transactions used in the prompt.
- `rule_violations`: warning/blocking controls.
- `review_queue`: cases requiring controller action.
- `review_decisions`: approved/corrected/rejected controller decisions.
- `evaluation_metrics`: quality and workflow metrics.

## Test

```powershell
ruff check .
pytest
```

## Current Limitations

- Historical retrieval uses TF-IDF by default; embeddings can be wired in through
  the retrieval interface.
- Review is file-based, not a web UI.
- The Azure OpenAI client is implemented, but real data use requires governance
  and privacy approval before enabling it.
- ERP integration is represented as CSV/Excel export, not direct database access.
