# Hermes

Hermes is a thin multi-app AI gateway.

It gives multiple apps one stable HTTP surface for:
- OpenAI-compatible providers
- Codex-backed execution through the local CLI
- schema-constrained JSON generation

Hermes is intentionally not an app-specific prompt service. Domain prompts stay in the calling app. Hermes owns provider routing, auth, retries/fallbacks, and response normalization.

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
