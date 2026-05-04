from __future__ import annotations

import json
import os
from collections import Counter
from typing import Protocol

from src.config.settings import LLMConfig
from src.utils.schemas import InvoiceRecord, LLMSuggestion, SimilarMatch


class PostingLLMClient(Protocol):
    model_name: str

    def suggest_posting(
        self,
        invoice: InvoiceRecord,
        matches: list[SimilarMatch],
        prompt: str,
        prompt_version: str,
    ) -> LLMSuggestion:
        """Return a structured posting suggestion."""


class MockLLMClient:
    model_name = "mock-llm"

    def suggest_posting(
        self,
        invoice: InvoiceRecord,
        matches: list[SimilarMatch],
        prompt: str,
        prompt_version: str,
    ) -> LLMSuggestion:
        if not matches:
            return LLMSuggestion(
                suggested_account=None,
                suggested_cost_center=invoice.cost_center,
                suggested_project_code=invoice.project_code,
                suggested_vat_code=invoice.vat_code,
                confidence=0.2,
                rationale="No historical examples were available.",
                uncertainty_flags=["no_similar_transactions"],
                referenced_historical_ids=[],
                prompt_version=prompt_version,
                model_name=self.model_name,
            )

        account = Counter(match.account_code for match in matches).most_common(1)[0][0]
        top_match = matches[0]
        avg_similarity = sum(match.similarity_score for match in matches) / len(matches)
        confidence = round(min(max(avg_similarity, 0.0), 0.95), 3)

        return LLMSuggestion(
            suggested_account=account,
            suggested_cost_center=invoice.cost_center or top_match.cost_center,
            suggested_project_code=invoice.project_code or top_match.project_code,
            suggested_vat_code=invoice.vat_code or top_match.vat_code,
            confidence=confidence,
            rationale="Suggested from top-k similar historical transactions.",
            uncertainty_flags=[] if confidence >= 0.75 else ["low_similarity"],
            referenced_historical_ids=[match.historical_id for match in matches],
            prompt_version=prompt_version,
            model_name=self.model_name,
        )


class AzureOpenAIClient:
    def __init__(self, config: LLMConfig) -> None:
        from openai import AzureOpenAI

        endpoint = os.getenv(config.azure_endpoint_env)
        api_key = os.getenv(config.azure_api_key_env)
        api_version = os.getenv(config.azure_api_version_env)
        deployment = os.getenv(config.azure_deployment_env)
        if not all([endpoint, api_key, api_version, deployment]):
            raise ValueError("Azure OpenAI environment variables are not fully configured.")

        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        self._deployment = deployment
        self.model_name = config.model_name

    def suggest_posting(
        self,
        invoice: InvoiceRecord,
        matches: list[SimilarMatch],
        prompt: str,
        prompt_version: str,
    ) -> LLMSuggestion:
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON for the requested bookkeeping suggestion.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        return LLMSuggestion(
            **payload,
            prompt_version=prompt_version,
            model_name=self.model_name,
            raw_response=payload,
        )


def build_llm_client(config: LLMConfig) -> PostingLLMClient:
    if config.provider == "azure_openai":
        return AzureOpenAIClient(config)
    return MockLLMClient()
