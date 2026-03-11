# Hermes

Hermes is a thin multi-app AI gateway.

It gives multiple apps one stable HTTP surface for:
- OpenAI-compatible providers
- Codex-backed execution through the local CLI
- schema-constrained JSON generation

Hermes is intentionally not an app-specific prompt service. Domain prompts stay in the calling app. Hermes owns provider routing, auth, retries/fallbacks, and response normalization.

## Configuration
Hermes groups env vars by responsibility:
- `HERMES_*` for gateway server behavior
- `OPENAI_COMPATIBLE_*` for OpenAI/OpenRouter/Gemini-compatible HTTP providers
- `CODEX_*` for Codex CLI execution

Example:

```env
# Hermes server
HERMES_SERVICE_TOKEN=local-dev-token
HERMES_DEFAULT_PROVIDER=codex_cli
HERMES_REQUEST_TIMEOUT_SECONDS=180

# OpenAI-compatible provider
OPENAI_COMPATIBLE_API_KEY=
OPENAI_COMPATIBLE_BASE_URL=https://openrouter.ai/api/v1
OPENAI_COMPATIBLE_MODEL=openai/gpt-4o-mini
OPENAI_COMPATIBLE_FALLBACK_MODELS=
OPENAI_COMPATIBLE_SITE_URL=http://localhost:8010
OPENAI_COMPATIBLE_APP_NAME=hermes

# Codex provider
CODEX_COMMAND=codex
CODEX_MODEL=
CODEX_PROFILE=
CODEX_SANDBOX=read-only
CODEX_TIMEOUT_SECONDS=180
CODEX_EXPECTED_VERSION=
CODEX_VERSION_STRICT=true
CODEX_FALLBACK_TO_OPENAI_COMPATIBLE=true
CODEX_WORKDIR=
```

Hermes still accepts the older `OPENROUTER_*`, `OPENAI_*`, `GEMINI_*`, and `CODEX_FALLBACK_TO_OPENAI` names as compatibility fallbacks, but the names above are the preferred public config surface.

## Endpoints
- `GET /health`
- `POST /v1/chat/completions`
- `POST /v1/structured`

## Runtime Model
- Docker-ready for API-key providers
- host-supported for Codex CLI
- stateless and env-configured in v1

## Quick Start
```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

## Docker
```bash
docker build -t hermes .
docker run --rm -p 8010:8010 --env-file .env hermes
```

Or with Compose:

```bash
docker compose up --build
```

For Codex-backed host usage, run Hermes on the same machine where `codex` is installed and logged in.

## Example
```bash
curl -s http://localhost:8010/v1/structured \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Return a JSON object with a greeting string."}],
    "schema": {
      "type": "object",
      "required": ["greeting"],
      "properties": {
        "greeting": {"type": "string"}
      },
      "additionalProperties": false
    }
  }'
```
