from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings


def require_service_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.service_token
    if not expected:
        raise HTTPException(status_code=500, detail="HERMES_SERVICE_TOKEN is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid bearer token.")

