# IT Runbook

## Purpose

Run the bookkeeping control workflow as a scheduled Python batch. The same
scripts can run locally, in Azure, or in Microsoft Fabric as long as the file
paths in `config/default.yaml` are available.

## Batch Order

```powershell
python -m src.run_batch --config config/default.yaml
python -m src.run_review_import --config config/default.yaml
python -m src.run_evaluation --config config/default.yaml
```

## Configuration

Use a copied YAML config for each environment. Configure:

- ERP input file path.
- Historical transaction file path.
- Output directory for Power BI.
- Review directory for controller files.
- LLM provider: `mock` or `azure_openai`.
- Top-k retrieval count.
- Confidence thresholds.

## Azure OpenAI

Only use `azure_openai` after the organization has approved handling of the
actual data. Configure these environment variables:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`

## Operational Controls

- Store generated outputs in a controlled workspace.
- Keep original suggestions and human corrections as separate records.
- Do not overwrite `llm_suggestions` with controller decisions.
- Monitor review rate, correction rate, stop rate, and low-confidence cases.
