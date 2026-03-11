import json

from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_service_token
from app.config import Settings, get_settings
from app.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    HealthResponse,
    StructuredRequest,
    StructuredResponse,
)
from app.services.gateway import GatewayError, GatewayService, get_gateway_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", default_provider=settings.default_provider)  # type: ignore[arg-type]


@router.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    dependencies=[Depends(require_service_token)],
)
def chat_completions(
    payload: ChatCompletionRequest,
    gateway: GatewayService = Depends(get_gateway_service),
) -> ChatCompletionResponse:
    try:
        result = gateway.chat(payload)
    except GatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatCompletionResponse(
        provider=result.provider,  # type: ignore[arg-type]
        used_model=result.used_model,
        content=result.content,
    )


@router.post(
    "/v1/structured",
    response_model=StructuredResponse,
    dependencies=[Depends(require_service_token)],
)
def structured_generation(
    payload: StructuredRequest,
    gateway: GatewayService = Depends(get_gateway_service),
) -> StructuredResponse:
    try:
        result = gateway.structured(payload)
    except GatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return StructuredResponse(
        provider=result.provider,  # type: ignore[arg-type]
        used_model=result.used_model,
        data=json.loads(result.content),
    )

