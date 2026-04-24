import pytest
from fastapi import HTTPException

from company_agent.common.auth import validate_internal_api_key


def test_validate_internal_api_key_accepts_matching_key() -> None:
    validate_internal_api_key(expected_key="secret", received_key="secret")


def test_validate_internal_api_key_rejects_wrong_key() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_internal_api_key(expected_key="secret", received_key="wrong")

    assert exc_info.value.status_code == 401


def test_validate_internal_api_key_requires_configuration() -> None:
    with pytest.raises(RuntimeError):
        validate_internal_api_key(expected_key="", received_key="secret")
