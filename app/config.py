import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    service_token: str
    default_provider: str
    openrouter_api_key: str
    openai_api_key: str
    gemini_api_key: str
    openai_base_url: str
    openai_model: str
    fallback_models: str
    openrouter_site_url: str
    openrouter_app_name: str
    codex_command: str
    codex_model: str
    codex_profile: str
    codex_sandbox: str
    codex_timeout_seconds: int
    codex_expected_version: str
    codex_version_strict: bool
    codex_fallback_to_openai: bool
    codex_workdir: str


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        service_token=os.getenv("HERMES_SERVICE_TOKEN", "").strip(),
        default_provider=os.getenv("HERMES_DEFAULT_PROVIDER", "openai_compatible").strip() or "openai_compatible",
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini").strip(),
        fallback_models=os.getenv("FALLBACK_MODELS", "").strip(),
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "http://localhost:8010").strip(),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "hermes").strip(),
        codex_command=os.getenv("CODEX_COMMAND", "codex").strip() or "codex",
        codex_model=os.getenv("CODEX_MODEL", "").strip(),
        codex_profile=os.getenv("CODEX_PROFILE", "").strip(),
        codex_sandbox=os.getenv("CODEX_SANDBOX", "read-only").strip() or "read-only",
        codex_timeout_seconds=int(os.getenv("CODEX_TIMEOUT_SECONDS", "180")),
        codex_expected_version=os.getenv("CODEX_EXPECTED_VERSION", "").strip(),
        codex_version_strict=_env_bool("CODEX_VERSION_STRICT", True),
        codex_fallback_to_openai=_env_bool("CODEX_FALLBACK_TO_OPENAI", True),
        codex_workdir=os.getenv("CODEX_WORKDIR", str(Path.cwd())).strip() or str(Path.cwd()),
    )

