from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, status


def validate_internal_api_key(expected_key: str, received_key: str | None) -> None:
    if not expected_key:
        raise RuntimeError("INTERNAL_API_KEY must be configured for internal services.")

    if received_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


def require_internal_api_key(expected_key: str):
    def dependency(
        x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-API-Key")] = None,
    ) -> None:
        validate_internal_api_key(expected_key=expected_key, received_key=x_internal_api_key)

    return dependency

