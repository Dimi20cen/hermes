import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _env_str(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value.strip()
    return default


@dataclass(frozen=True)
class Settings:
    service_token: str
    default_provider: str
    request_timeout_seconds: int
    openai_compatible_api_key: str
    openai_compatible_base_url: str
    openai_compatible_model: str
    openai_compatible_fallback_models: str
    openai_compatible_site_url: str
    openai_compatible_app_name: str
    codex_command: str
    codex_model: str
    codex_profile: str
    codex_sandbox: str
    codex_timeout_seconds: int
    codex_expected_version: str
    codex_version_strict: bool
    codex_fallback_to_openai_compatible: bool
    codex_workdir: str


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        service_token=_env_str("HERMES_SERVICE_TOKEN"),
        default_provider=_env_str("HERMES_DEFAULT_PROVIDER", default="openai_compatible") or "openai_compatible",
        request_timeout_seconds=int(_env_str("HERMES_REQUEST_TIMEOUT_SECONDS", default="180")),
        openai_compatible_api_key=_env_str(
            "OPENAI_COMPATIBLE_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
        ),
        openai_compatible_base_url=_env_str(
            "OPENAI_COMPATIBLE_BASE_URL",
            "OPENAI_BASE_URL",
            default="https://openrouter.ai/api/v1",
        ),
        openai_compatible_model=_env_str(
            "OPENAI_COMPATIBLE_MODEL",
            "OPENAI_MODEL",
            default="openai/gpt-4o-mini",
        ),
        openai_compatible_fallback_models=_env_str(
            "OPENAI_COMPATIBLE_FALLBACK_MODELS",
            "FALLBACK_MODELS",
        ),
        openai_compatible_site_url=_env_str(
            "OPENAI_COMPATIBLE_SITE_URL",
            "OPENROUTER_SITE_URL",
            default="http://localhost:8010",
        ),
        openai_compatible_app_name=_env_str(
            "OPENAI_COMPATIBLE_APP_NAME",
            "OPENROUTER_APP_NAME",
            default="hermes",
        ),
        codex_command=_env_str("CODEX_COMMAND", default="codex") or "codex",
        codex_model=_env_str("CODEX_MODEL"),
        codex_profile=_env_str("CODEX_PROFILE"),
        codex_sandbox=_env_str("CODEX_SANDBOX", default="read-only") or "read-only",
        codex_timeout_seconds=int(os.getenv("CODEX_TIMEOUT_SECONDS", "180")),
        codex_expected_version=_env_str("CODEX_EXPECTED_VERSION"),
        codex_version_strict=_env_bool("CODEX_VERSION_STRICT", True),
        codex_fallback_to_openai_compatible=_env_bool("CODEX_FALLBACK_TO_OPENAI_COMPATIBLE", _env_bool("CODEX_FALLBACK_TO_OPENAI", True)),
        codex_workdir=_env_str("CODEX_WORKDIR", default=str(Path.cwd())) or str(Path.cwd()),
    )
