from logging import Logger
from uuid import UUID

from app.database import DbSession
from app.models import DataSource, ProviderPriority
from app.repositories import (
    DataSourceRepository,
    ProviderPriorityRepository,
    UserProviderPriorityRepository,
)
from app.repositories.device_type_priority_repository import DeviceTypePriorityRepository
from app.schemas.enums import DeviceType, ProviderName
from app.schemas.model_crud.data_priority import (
    DataSourceListResponse,
    DataSourceResponse,
    DeviceTypePriorityBulkUpdate,
    DeviceTypePriorityListResponse,
    DeviceTypePriorityResponse,
    EffectiveProviderPriorityItem,
    EffectiveProviderPriorityListResponse,
    ProviderPriorityBulkUpdate,
    ProviderPriorityListResponse,
    ProviderPriorityResponse,
    UserProviderPriorityBulkUpdate,
    UserProviderPriorityResponse,
)
from app.utils.exceptions import handle_exceptions


class PriorityService:
    def __init__(self, log: Logger):
        self.logger = log
        self.priority_repo = ProviderPriorityRepository(ProviderPriority)
        self.user_priority_repo = UserProviderPriorityRepository()
        self.device_type_priority_repo = DeviceTypePriorityRepository()
        self.data_source_repo = DataSourceRepository(DataSource)

    @handle_exceptions
    def get_provider_priorities(
        self,
        db_session: DbSession,
    ) -> ProviderPriorityListResponse:
        priorities = self.priority_repo.get_all_ordered(db_session)
        return ProviderPriorityListResponse(items=[ProviderPriorityResponse.model_validate(p) for p in priorities])

    @handle_exceptions
    def update_provider_priority(
        self,
        db_session: DbSession,
        provider: ProviderName,
        priority: int,
    ) -> ProviderPriorityResponse:
        result = self.priority_repo.upsert(db_session, provider, priority)
        db_session.commit()
        return ProviderPriorityResponse.model_validate(result)

    @handle_exceptions
    def bulk_update_priorities(
        self,
        db_session: DbSession,
        update: ProviderPriorityBulkUpdate,
    ) -> ProviderPriorityListResponse:
        priorities_tuples = [(p.provider, p.priority) for p in update.priorities]
        results = self.priority_repo.bulk_update(db_session, priorities_tuples)
        db_session.commit()
        return ProviderPriorityListResponse(items=[ProviderPriorityResponse.model_validate(p) for p in results])

    @handle_exceptions
    def get_user_data_sources(
        self,
        db_session: DbSession,
        user_id: UUID,
    ) -> DataSourceListResponse:
        sources = self.data_source_repo.get_user_data_sources(db_session, user_id)
        items = [
            DataSourceResponse(
                id=ds.id,
                user_id=ds.user_id,
                provider=ds.provider,
                user_connection_id=ds.user_connection_id,
                device_model=ds.device_model,
                software_version=ds.software_version,
                source=ds.source,
                device_type=ds.device_type,
                original_source_name=ds.original_source_name,
                display_name=self._build_display_name(ds),
            )
            for ds in sources
        ]
        return DataSourceListResponse(items=items, total=len(items))

    @handle_exceptions
    def get_device_type_priorities(
        self,
        db_session: DbSession,
    ) -> DeviceTypePriorityListResponse:
        priorities = self.device_type_priority_repo.get_all_ordered(db_session)
        return DeviceTypePriorityListResponse(items=[DeviceTypePriorityResponse.model_validate(p) for p in priorities])

    @handle_exceptions
    def update_device_type_priority(
        self,
        db_session: DbSession,
        device_type: DeviceType,
        priority: int,
    ) -> DeviceTypePriorityResponse:
        result = self.device_type_priority_repo.upsert(db_session, device_type, priority)
        db_session.commit()
        return DeviceTypePriorityResponse.model_validate(result)

    @handle_exceptions
    def bulk_update_device_type_priorities(
        self,
        db_session: DbSession,
        update: DeviceTypePriorityBulkUpdate,
    ) -> DeviceTypePriorityListResponse:
        priorities_tuples = [(p.device_type, p.priority) for p in update.priorities]
        results = self.device_type_priority_repo.bulk_update(db_session, priorities_tuples)
        db_session.commit()
        return DeviceTypePriorityListResponse(items=[DeviceTypePriorityResponse.model_validate(p) for p in results])

    @handle_exceptions
    def get_effective_user_provider_priorities(
        self,
        db_session: DbSession,
        user_id: UUID,
    ) -> EffectiveProviderPriorityListResponse:
        """Return merged priority list: user overrides win, global fills the rest."""
        effective = self._resolve_effective_order(db_session, user_id)
        items = [EffectiveProviderPriorityItem(provider=p, priority=pri, source=src) for p, pri, src in effective]
        return EffectiveProviderPriorityListResponse(items=items)

    @handle_exceptions
    def update_user_provider_priority(
        self,
        db_session: DbSession,
        user_id: UUID,
        provider: ProviderName,
        priority: int,
    ) -> UserProviderPriorityResponse:
        result = self.user_priority_repo.upsert(db_session, user_id, provider, priority)
        db_session.commit()
        return UserProviderPriorityResponse.model_validate(result)

    @handle_exceptions
    def bulk_update_user_provider_priorities(
        self,
        db_session: DbSession,
        user_id: UUID,
        update: UserProviderPriorityBulkUpdate,
    ) -> EffectiveProviderPriorityListResponse:
        tuples = [(p.provider, p.priority) for p in update.priorities]
        self.user_priority_repo.bulk_update(db_session, user_id, tuples)
        db_session.commit()
        return self.get_effective_user_provider_priorities(db_session, user_id)

    @handle_exceptions
    def reset_user_provider_priority(
        self,
        db_session: DbSession,
        user_id: UUID,
        provider: ProviderName,
    ) -> EffectiveProviderPriorityListResponse:
        """Remove a user's override for one provider, reverting to global default."""
        self.user_priority_repo.delete_by_provider(db_session, user_id, provider)
        db_session.commit()
        return self.get_effective_user_provider_priorities(db_session, user_id)

    def _resolve_effective_order(
        self,
        db_session: DbSession,
        user_id: UUID,
    ) -> list[tuple[ProviderName, int, str]]:
        global_order = self.priority_repo.get_priority_order(db_session)
        user_overrides = {p.provider: p.priority for p in self.user_priority_repo.get_all_for_user(db_session, user_id)}
        merged: dict[ProviderName, tuple[int, str]] = {p: (pri, "global") for p, pri in global_order.items()}
        for p, pri in user_overrides.items():
            merged[p] = (pri, "user")
        return sorted(
            [(p, pri, src) for p, (pri, src) in merged.items()],
            key=lambda row: row[1],
        )

    def get_priority_data_source_ids(
        self,
        db_session: DbSession,
        user_id: UUID,
    ) -> list[UUID]:
        """Get data source IDs for a user, ordered by effective (user-override-aware) priority."""
        provider_order = {p: pri for p, pri, _ in self._resolve_effective_order(db_session, user_id)}
        device_type_order = self.device_type_priority_repo.get_priority_order(db_session)
        sources = self.data_source_repo.get_user_data_sources(db_session, user_id)

        if not sources:
            return []

        def sort_key(ds: DataSource) -> tuple[int, int, str]:
            provider_priority = provider_order.get(ds.provider, 99)
            device_type_priority = 99
            if ds.device_type:
                try:
                    dt = DeviceType(ds.device_type)
                    device_type_priority = device_type_order.get(dt, 99)
                except ValueError:
                    pass
            return (provider_priority, device_type_priority, ds.device_model or "")

        sorted_sources = sorted(sources, key=sort_key)
        return [ds.id for ds in sorted_sources]

    def get_best_data_source_id(
        self,
        db_session: DbSession,
        user_id: UUID,
    ) -> UUID | None:
        ids = self.get_priority_data_source_ids(db_session, user_id)
        return ids[0] if ids else None

    def _build_display_name(self, ds: DataSource) -> str:
        parts = []
        if ds.provider:
            parts.append(ds.provider.value.capitalize())
        if ds.device_model:
            parts.append(ds.device_model)
        elif ds.original_source_name:
            parts.append(ds.original_source_name)
        return " - ".join(parts) if parts else "Unknown Source"
