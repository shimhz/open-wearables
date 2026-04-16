"""API endpoints for managing global provider priorities and per-user overrides."""

from logging import getLogger
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path

from app.database import DbSession
from app.schemas.enums import DeviceType, ProviderName
from app.schemas.model_crud.data_priority import (
    DeviceTypePriorityBulkUpdate,
    DeviceTypePriorityListResponse,
    DeviceTypePriorityResponse,
    DeviceTypePriorityUpdate,
    EffectiveProviderPriorityListResponse,
    ProviderPriorityBulkUpdate,
    ProviderPriorityListResponse,
    ProviderPriorityResponse,
    ProviderPriorityUpdate,
    UserProviderPriorityBulkUpdate,
    UserProviderPriorityResponse,
    UserProviderPriorityUpdate,
)
from app.services import ApiKeyDep, DeveloperDep, PriorityService

router = APIRouter()
priority_service = PriorityService(log=getLogger(__name__))


@router.get(
    "/priorities/providers",
    summary="Get global provider priorities",
)
def get_provider_priorities(
    db: DbSession,
    _developer: DeveloperDep,
) -> ProviderPriorityListResponse:
    return priority_service.get_provider_priorities(db)


@router.put(
    "/priorities/providers/{provider}",
    summary="Update provider priority",
)
def update_provider_priority(
    db: DbSession,
    _developer: DeveloperDep,
    provider: Annotated[ProviderName, Path(description="Provider name enum")],
    update: ProviderPriorityUpdate,
) -> ProviderPriorityResponse:
    return priority_service.update_provider_priority(db, provider, update.priority)


@router.put(
    "/priorities/providers",
    summary="Bulk update provider priorities",
)
def bulk_update_provider_priorities(
    db: DbSession,
    _developer: DeveloperDep,
    update: ProviderPriorityBulkUpdate,
) -> ProviderPriorityListResponse:
    return priority_service.bulk_update_priorities(db, update)


@router.get(
    "/users/{user_id}/priorities/providers",
    summary="Get effective provider priorities for a user",
)
def get_user_provider_priorities(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
) -> EffectiveProviderPriorityListResponse:
    """Returns the user's effective provider order.

    Each item indicates whether its priority came from a user override
    (`source: "user"`) or the global default (`source: "global"`).
    """
    return priority_service.get_effective_user_provider_priorities(db, user_id)


@router.put(
    "/users/{user_id}/priorities/providers/{provider}",
    summary="Set user override for one provider",
)
def update_user_provider_priority(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    provider: Annotated[ProviderName, Path(description="Provider name enum")],
    update: UserProviderPriorityUpdate,
) -> UserProviderPriorityResponse:
    return priority_service.update_user_provider_priority(db, user_id, provider, update.priority)


@router.put(
    "/users/{user_id}/priorities/providers",
    summary="Bulk set user overrides for providers",
)
def bulk_update_user_provider_priorities(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    update: UserProviderPriorityBulkUpdate,
) -> EffectiveProviderPriorityListResponse:
    return priority_service.bulk_update_user_provider_priorities(db, user_id, update)


@router.delete(
    "/users/{user_id}/priorities/providers/{provider}",
    summary="Reset one provider back to the global default",
)
def reset_user_provider_priority(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    provider: Annotated[ProviderName, Path(description="Provider name enum")],
) -> EffectiveProviderPriorityListResponse:
    return priority_service.reset_user_provider_priority(db, user_id, provider)


@router.get(
    "/priorities/device-types",
    summary="Get device type priorities",
)
def get_device_type_priorities(
    db: DbSession,
    _developer: DeveloperDep,
) -> DeviceTypePriorityListResponse:
    return priority_service.get_device_type_priorities(db)


@router.put(
    "/priorities/device-types/{device_type}",
    summary="Update device type priority",
)
def update_device_type_priority(
    db: DbSession,
    _developer: DeveloperDep,
    device_type: Annotated[DeviceType, Path(description="Device type enum")],
    update: DeviceTypePriorityUpdate,
) -> DeviceTypePriorityResponse:
    return priority_service.update_device_type_priority(db, device_type, update.priority)


@router.put(
    "/priorities/device-types",
    summary="Bulk update device type priorities",
)
def bulk_update_device_type_priorities(
    db: DbSession,
    _developer: DeveloperDep,
    update: DeviceTypePriorityBulkUpdate,
) -> DeviceTypePriorityListResponse:
    return priority_service.bulk_update_device_type_priorities(db, update)
