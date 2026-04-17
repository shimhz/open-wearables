"""Tests for UserScopedAuthDep (require_user_scope)."""

from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import SDKAuthContext
from app.utils.auth import require_user_scope
from tests.factories import ApiKeyFactory

USER_A = UUID("123e4567-e89b-12d3-a456-426614174000")
USER_B = UUID("123e4567-e89b-12d3-a456-426614174001")


class TestRequireUserScope:
    @pytest.mark.asyncio
    async def test_sdk_token_matching_user_id(self, db: Session) -> None:
        auth = SDKAuthContext(auth_type="sdk_token", user_id=USER_A, app_id="app_1")
        result = await require_user_scope(user_id=USER_A, auth=auth)
        assert result.auth_type == "sdk_token"
        assert result.user_id == USER_A

    @pytest.mark.asyncio
    async def test_sdk_token_mismatched_user_id_raises_403(self, db: Session) -> None:
        auth = SDKAuthContext(auth_type="sdk_token", user_id=USER_A, app_id="app_1")
        with pytest.raises(HTTPException) as exc:
            await require_user_scope(user_id=USER_B, auth=auth)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sdk_token_missing_user_id_raises_403(self, db: Session) -> None:
        auth = SDKAuthContext(auth_type="sdk_token", user_id=None, app_id="app_1")
        with pytest.raises(HTTPException) as exc:
            await require_user_scope(user_id=USER_A, auth=auth)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_api_key_passes_for_any_user_id(self, db: Session) -> None:
        api_key = ApiKeyFactory()
        auth = SDKAuthContext(auth_type="api_key", api_key_id=api_key.id)
        result = await require_user_scope(user_id=USER_A, auth=auth)
        assert result.auth_type == "api_key"

    @pytest.mark.asyncio
    async def test_api_key_passes_for_random_user_id(self, db: Session) -> None:
        api_key = ApiKeyFactory()
        auth = SDKAuthContext(auth_type="api_key", api_key_id=api_key.id)
        result = await require_user_scope(user_id=uuid4(), auth=auth)
        assert result.auth_type == "api_key"
