from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import asc
from sqlalchemy.dialects.postgresql import insert

from app.database import DbSession
from app.models import UserProviderPriority
from app.schemas.enums import ProviderName


class UserProviderPriorityRepository:
    def __init__(self, model: type[UserProviderPriority] = UserProviderPriority):
        self.model = model

    def get_all_for_user(self, db_session: DbSession, user_id: UUID) -> list[UserProviderPriority]:
        return (
            db_session.query(self.model).filter(self.model.user_id == user_id).order_by(asc(self.model.priority)).all()
        )

    def get_by_provider(
        self,
        db_session: DbSession,
        user_id: UUID,
        provider: ProviderName,
    ) -> UserProviderPriority | None:
        return (
            db_session.query(self.model)
            .filter(self.model.user_id == user_id, self.model.provider == provider)
            .one_or_none()
        )

    def upsert(
        self,
        db_session: DbSession,
        user_id: UUID,
        provider: ProviderName,
        priority: int,
    ) -> UserProviderPriority:
        now = datetime.now(timezone.utc)
        stmt = (
            insert(self.model)
            .values(
                id=uuid4(),
                user_id=user_id,
                provider=provider,
                priority=priority,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_user_provider_priority",
                set_={"priority": priority, "updated_at": now},
            )
        )
        db_session.execute(stmt)
        db_session.flush()
        return self.get_by_provider(db_session, user_id, provider)  # type: ignore[return-value]

    def bulk_update(
        self,
        db_session: DbSession,
        user_id: UUID,
        priorities: list[tuple[ProviderName, int]],
    ) -> list[UserProviderPriority]:
        now = datetime.now(timezone.utc)
        for provider, priority in priorities:
            stmt = (
                insert(self.model)
                .values(
                    id=uuid4(),
                    user_id=user_id,
                    provider=provider,
                    priority=priority,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    constraint="uq_user_provider_priority",
                    set_={"priority": priority, "updated_at": now},
                )
            )
            db_session.execute(stmt)
        db_session.flush()
        return self.get_all_for_user(db_session, user_id)

    def delete_by_provider(
        self,
        db_session: DbSession,
        user_id: UUID,
        provider: ProviderName,
    ) -> bool:
        deleted = (
            db_session.query(self.model)
            .filter(self.model.user_id == user_id, self.model.provider == provider)
            .delete(synchronize_session=False)
        )
        db_session.flush()
        return deleted > 0
