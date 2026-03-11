from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_gateway_service, get_settings
from app.config import Settings
from app.providers.base import ProviderResult


class FakeGatewayService:
    def chat(self, payload):
        return ProviderResult(provider="openai_compatible", used_model="test-model", content="hello")

    def structured(self, payload):
        return ProviderResult(
            provider="openai_compatible",
            used_model="test-model",
            content='{"greeting":"hello"}',
        )


def build_settings() -> Settings:
    return Settings(
        service_token="test-token",
        default_provider="openai_compatible",
        request_timeout_seconds=180,
        openai_compatible_api_key="",
        openai_compatible_base_url="https://openrouter.ai/api/v1",
        openai_compatible_model="openai/gpt-4o-mini",
        openai_compatible_fallback_models="",
        openai_compatible_site_url="http://localhost:8010",
        openai_compatible_app_name="hermes",
        codex_command="codex",
        codex_model="",
        codex_profile="",
        codex_sandbox="read-only",
        codex_timeout_seconds=180,
        codex_expected_version="",
        codex_version_strict=True,
        codex_fallback_to_openai_compatible=True,
        codex_workdir="/tmp",
    )


def test_health_is_public() -> None:
    app.dependency_overrides[get_settings] = build_settings
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    app.dependency_overrides.clear()


def test_auth_is_required() -> None:
    app.dependency_overrides[get_settings] = build_settings
    client = TestClient(app)
    response = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_chat_completion() -> None:
    app.dependency_overrides[get_settings] = build_settings
    app.dependency_overrides[get_gateway_service] = FakeGatewayService
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-token"},
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "hello"
    app.dependency_overrides.clear()


def test_structured_generation() -> None:
    app.dependency_overrides[get_settings] = build_settings
    app.dependency_overrides[get_gateway_service] = FakeGatewayService
    client = TestClient(app)
    response = client.post(
        "/v1/structured",
        headers={"Authorization": "Bearer test-token"},
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "schema": {
                "type": "object",
                "required": ["greeting"],
                "properties": {"greeting": {"type": "string"}},
                "additionalProperties": False,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["greeting"] == "hello"
    app.dependency_overrides.clear()
