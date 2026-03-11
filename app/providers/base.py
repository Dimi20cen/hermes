from dataclasses import dataclass
from typing import Protocol

from app.schemas import Message


class ProviderError(Exception):
    pass


@dataclass(frozen=True)
class ProviderRequest:
    messages: list[Message]
    model: str | None
    temperature: float


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    used_model: str
    content: str


class Provider(Protocol):
    name: str

    def chat(self, request: ProviderRequest) -> ProviderResult:
        ...

    def structured(self, request: ProviderRequest, schema: dict) -> ProviderResult:
        ...

