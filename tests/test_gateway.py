from app.config import Settings
from app.providers.base import ProviderError, ProviderRequest, ProviderResult
from app.schemas import ChatCompletionRequest, Message, StructuredRequest
from app.services.gateway import GatewayError, GatewayService


class FakeProvider:
    def __init__(self, name: str, result: ProviderResult | None = None, error: str | None = None):
        self.name = name
        self.result = result
        self.error = error

    def chat(self, request: ProviderRequest) -> ProviderResult:
        if self.error:
            raise ProviderError(self.error)
        assert self.result is not None
        return self.result

    def structured(self, request: ProviderRequest, schema: dict) -> ProviderResult:
        if self.error:
            raise ProviderError(self.error)
        assert self.result is not None
        return self.result


def build_settings(codex_fallback_to_openai: bool = True) -> Settings:
    return Settings(
        service_token="test-token",
        default_provider="openai_compatible",
        openrouter_api_key="",
        openai_api_key="",
        gemini_api_key="",
        openai_base_url="https://openrouter.ai/api/v1",
        openai_model="openai/gpt-4o-mini",
        fallback_models="",
        openrouter_site_url="http://localhost:8010",
        openrouter_app_name="hermes",
        codex_command="codex",
        codex_model="",
        codex_profile="",
        codex_sandbox="read-only",
        codex_timeout_seconds=180,
        codex_expected_version="",
        codex_version_strict=True,
        codex_fallback_to_openai=codex_fallback_to_openai,
        codex_workdir="/tmp",
    )


def test_structured_validates_schema() -> None:
    service = GatewayService(
        build_settings(),
        providers={
            "openai_compatible": FakeProvider(
                "openai_compatible",
                ProviderResult("openai_compatible", "test-model", '{"score": 42}'),
            ),
            "codex_cli": FakeProvider("codex_cli", ProviderResult("codex_cli", "codex", '{"score": 42}')),
        },
    )
    result = service.structured(
        StructuredRequest(
            messages=[Message(role="user", content="score it")],
            output_schema={
                "type": "object",
                "required": ["score"],
                "properties": {"score": {"type": "integer"}},
                "additionalProperties": False,
            },
        )
    )
    assert result.used_model == "test-model"


def test_structured_rejects_schema_mismatch() -> None:
    service = GatewayService(
        build_settings(),
        providers={
            "openai_compatible": FakeProvider(
                "openai_compatible",
                ProviderResult("openai_compatible", "test-model", '{"score": "wrong"}'),
            ),
            "codex_cli": FakeProvider("codex_cli", ProviderResult("codex_cli", "codex", '{"score": "wrong"}')),
        },
    )
    try:
        service.structured(
            StructuredRequest(
                messages=[Message(role="user", content="score it")],
                output_schema={
                    "type": "object",
                    "required": ["score"],
                    "properties": {"score": {"type": "integer"}},
                    "additionalProperties": False,
                },
            )
        )
    except GatewayError as exc:
        assert "must be an integer" in str(exc)
    else:
        raise AssertionError("Expected schema validation failure")


def test_codex_falls_back_to_openai() -> None:
    service = GatewayService(
        build_settings(codex_fallback_to_openai=True),
        providers={
            "openai_compatible": FakeProvider(
                "openai_compatible",
                ProviderResult("openai_compatible", "fallback-model", "fallback"),
            ),
            "codex_cli": FakeProvider("codex_cli", error="codex unavailable"),
        },
    )
    result = service.chat(
        ChatCompletionRequest(
            provider="codex_cli",
            messages=[Message(role="user", content="hi")],
        )
    )
    assert result.used_model == "fallback-model"


def test_codex_no_fallback_raises() -> None:
    service = GatewayService(
        build_settings(codex_fallback_to_openai=False),
        providers={
            "openai_compatible": FakeProvider(
                "openai_compatible",
                ProviderResult("openai_compatible", "fallback-model", "fallback"),
            ),
            "codex_cli": FakeProvider("codex_cli", error="codex unavailable"),
        },
    )
    try:
        service.chat(
            ChatCompletionRequest(
                provider="codex_cli",
                messages=[Message(role="user", content="hi")],
            )
        )
    except GatewayError as exc:
        assert "codex unavailable" in str(exc)
    else:
        raise AssertionError("Expected codex failure")
