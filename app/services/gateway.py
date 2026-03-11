import json
from functools import lru_cache
from typing import Any

from app.config import Settings, get_settings
from app.core_json_schema import SchemaValidationError, validate_json_schema
from app.providers.base import Provider, ProviderError, ProviderRequest, ProviderResult
from app.providers.codex_cli import CodexCLIProvider
from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas import ChatCompletionRequest, StructuredRequest


class GatewayError(Exception):
    pass


def _extract_json(content: str) -> Any:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.replace("json", "", 1).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise GatewayError("Provider did not return valid JSON.") from exc


class GatewayService:
    def __init__(self, settings: Settings, providers: dict[str, Provider] | None = None):
        self.settings = settings
        self.providers = providers or {
            "openai_compatible": OpenAICompatibleProvider(settings),
            "codex_cli": CodexCLIProvider(settings),
        }

    def _resolve_provider(self, requested: str | None) -> Provider:
        provider_name = requested or self.settings.default_provider
        provider = self.providers.get(provider_name)
        if provider is None:
            raise GatewayError(f"Unsupported provider '{provider_name}'.")
        return provider

    def _call_with_fallback(
        self,
        provider_name: str | None,
        call: str,
        request: ProviderRequest,
        schema: dict[str, Any] | None = None,
    ) -> ProviderResult:
        provider = self._resolve_provider(provider_name)
        try:
            if call == "chat":
                return provider.chat(request)
            return provider.structured(request, schema or {})
        except ProviderError as exc:
            if provider.name != "codex_cli" or not self.settings.codex_fallback_to_openai:
                raise GatewayError(str(exc)) from exc
            fallback = self.providers["openai_compatible"]
            try:
                if call == "chat":
                    return fallback.chat(request)
                return fallback.structured(request, schema or {})
            except ProviderError as fallback_exc:
                raise GatewayError(
                    f"Codex failed ({exc}); OpenAI-compatible fallback also failed ({fallback_exc})."
                ) from fallback_exc

    def chat(self, payload: ChatCompletionRequest) -> ProviderResult:
        request = ProviderRequest(
            messages=payload.messages,
            model=payload.model,
            temperature=payload.temperature,
        )
        return self._call_with_fallback(payload.provider, "chat", request)

    def structured(self, payload: StructuredRequest) -> ProviderResult:
        request = ProviderRequest(
            messages=payload.messages,
            model=payload.model,
            temperature=payload.temperature,
        )
        result = self._call_with_fallback(payload.provider, "structured", request, payload.output_schema)
        data = _extract_json(result.content)
        try:
            validate_json_schema(data, payload.output_schema)
        except SchemaValidationError as exc:
            raise GatewayError(str(exc)) from exc
        return ProviderResult(provider=result.provider, used_model=result.used_model, content=json.dumps(data))


@lru_cache(maxsize=1)
def get_gateway_service() -> GatewayService:
    return GatewayService(get_settings())
