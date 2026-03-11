from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["system", "user", "assistant"]
ProviderName = Literal["openai_compatible", "codex_cli"]


class HealthResponse(BaseModel):
    status: str
    default_provider: ProviderName


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class ChatCompletionRequest(BaseModel):
    messages: list[Message] = Field(min_length=1)
    provider: ProviderName | None = None
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class ChatCompletionResponse(BaseModel):
    provider: ProviderName
    used_model: str
    content: str


class StructuredRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    messages: list[Message] = Field(min_length=1)
    output_schema: dict[str, Any] = Field(alias="schema", serialization_alias="schema")
    provider: ProviderName | None = None
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class StructuredResponse(BaseModel):
    provider: ProviderName
    used_model: str
    data: Any
