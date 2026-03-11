import json
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.providers.base import ProviderError, ProviderRequest, ProviderResult
from app.schemas import Message


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _api_key(self) -> str:
        api_key = self.settings.openai_compatible_api_key
        if not api_key:
            raise ProviderError("OPENAI_COMPATIBLE_API_KEY is not configured.")
        return api_key

    def _model_chain(self, requested_model: str | None) -> list[str]:
        if requested_model:
            return [requested_model]
        fallbacks = [item.strip() for item in self.settings.openai_compatible_fallback_models.split(",") if item.strip()]
        models: list[str] = []
        for model in [self.settings.openai_compatible_model, *fallbacks]:
            if model and model not in models:
                models.append(model)
        return models

    def _client(self) -> OpenAI:
        return OpenAI(api_key=self._api_key(), base_url=self.settings.openai_compatible_base_url)

    def _request_kwargs(self, request: ProviderRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
        }
        if "openrouter.ai" in self.settings.openai_compatible_base_url:
            kwargs["extra_headers"] = {
                "HTTP-Referer": self.settings.openai_compatible_site_url,
                "X-Title": self.settings.openai_compatible_app_name,
            }
        return kwargs

    def chat(self, request: ProviderRequest) -> ProviderResult:
        client = self._client()
        request_kwargs = self._request_kwargs(request)
        last_error: Exception | None = None
        for model in self._model_chain(request.model):
            try:
                response = client.chat.completions.create(**request_kwargs, model=model)
                content = (response.choices[0].message.content or "").strip()
                if not content:
                    raise ProviderError("Provider returned an empty completion.")
                return ProviderResult(provider=self.name, used_model=model, content=content)
            except Exception as exc:  # pragma: no cover - exercised through fallback path
                last_error = exc
        raise ProviderError(f"OpenAI-compatible provider call failed: {last_error}")

    def structured(self, request: ProviderRequest, schema: dict) -> ProviderResult:
        client = self._client()
        schema_text = json.dumps(schema, ensure_ascii=True)
        request_kwargs = self._request_kwargs(
            ProviderRequest(
                messages=[
                    Message(
                        role="system",
                        content="Return only valid JSON matching the provided schema.",
                    ),
                    *request.messages,
                    Message(
                        role="system",
                        content=f"JSON schema:\n{schema_text}",
                    ),
                ],
                model=request.model,
                temperature=request.temperature,
            )
        )
        last_error: Exception | None = None
        for model in self._model_chain(request.model):
            try:
                response = client.chat.completions.create(
                    **request_kwargs,
                    model=model,
                    response_format={"type": "json_object"},
                )
                content = (response.choices[0].message.content or "").strip()
                if not content:
                    raise ProviderError("Provider returned an empty structured response.")
                return ProviderResult(provider=self.name, used_model=model, content=content)
            except Exception:
                try:
                    response = client.chat.completions.create(**request_kwargs, model=model)
                    content = (response.choices[0].message.content or "").strip()
                    if not content:
                        raise ProviderError("Provider returned an empty structured response.")
                    return ProviderResult(provider=self.name, used_model=model, content=content)
                except Exception as exc:
                    last_error = exc
        raise ProviderError(f"OpenAI-compatible structured call failed: {last_error}")
