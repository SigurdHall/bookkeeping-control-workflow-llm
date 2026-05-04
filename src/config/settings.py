from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class PathsConfig(BaseModel):
    input_path: Path = Path("data/input/invoices.csv")
    historical_path: Path = Path("data/synthetic/historical_records.json")
    output_dir: Path = Path("data/output")
    review_dir: Path = Path("data/review")
    review_input_path: Path = Path("data/review/review_decisions.csv")
    evaluation_output_dir: Path = Path("data/output")


class RetrievalConfig(BaseModel):
    top_k: int = 3
    method: Literal["tfidf", "embeddings"] = "tfidf"


class LLMConfig(BaseModel):
    provider: Literal["mock", "azure_openai"] = "mock"
    model_name: str = "mock-llm"
    prompt_version: str = "rag-posting-v1"
    azure_endpoint_env: str = "AZURE_OPENAI_ENDPOINT"
    azure_api_key_env: str = "AZURE_OPENAI_API_KEY"
    azure_api_version_env: str = "AZURE_OPENAI_API_VERSION"
    azure_deployment_env: str = "AZURE_OPENAI_CHAT_DEPLOYMENT"


class ThresholdConfig(BaseModel):
    suggest_min_confidence: float = 0.75
    review_min_confidence: float = 0.35
    warning_confidence_penalty: float = 0.15


class OutputConfig(BaseModel):
    write_csv: bool = True
    write_parquet: bool = True


class AppConfig(BaseModel):
    paths: PathsConfig = PathsConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    llm: LLMConfig = LLMConfig()
    thresholds: ThresholdConfig = ThresholdConfig()
    outputs: OutputConfig = OutputConfig()


def load_config(path: str | Path = "config/default.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return AppConfig(**data)
