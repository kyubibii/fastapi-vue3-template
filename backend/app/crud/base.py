import csv
import io
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")
FilterT = TypeVar("FilterT")
PKT = TypeVar("PKT")


class CRUDServiceBase(Generic[ModelT, CreateSchemaT, UpdateSchemaT, FilterT, PKT]):
    model: type[ModelT]
    id_field: str = "id"
    list_order_by: Any | None = None
    export_order_by: Any | None = None
    soft_delete: bool = True
    audit_fields: bool = True
    export_fields: list[str] = []
    export_filename: str = "export.csv"

    def build_base_query(self) -> Any:
        query = select(self.model)
        if self.soft_delete and hasattr(self.model, "is_deleted"):
            is_deleted = cast(Any, self.model).is_deleted
            query = query.where(is_deleted.is_(False))
        return query

    def apply_filters(self, query: Any, filters: FilterT | None) -> Any:
        return query

    def build_create_data(
        self, obj_in: CreateSchemaT, **extra_fields: Any
    ) -> dict[str, Any]:
        data = cast(dict[str, Any], cast(Any, obj_in).model_dump())
        data.update(extra_fields)
        return data

    def apply_update_data(self, db_obj: ModelT, obj_in: UpdateSchemaT) -> None:
        update_data = cast(
            dict[str, Any],
            cast(Any, obj_in).model_dump(exclude_unset=True),
        )
        for key, value in update_data.items():
            setattr(db_obj, key, value)

    async def before_create(
        self,
        *,
        session: AsyncSession,
        obj_in: CreateSchemaT,
        create_data: dict[str, Any],
    ) -> None:
        return None

    async def after_create(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
        obj_in: CreateSchemaT,
    ) -> None:
        return None

    async def before_update(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
        obj_in: UpdateSchemaT,
    ) -> None:
        return None

    async def after_update(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
        obj_in: UpdateSchemaT,
    ) -> None:
        return None

    async def before_delete(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
    ) -> None:
        return None

    async def after_delete(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
    ) -> None:
        return None

    async def get_by_id(self, *, session: AsyncSession, obj_id: PKT) -> ModelT | None:
        query = self.build_base_query().where(
            getattr(cast(Any, self.model), self.id_field) == obj_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        session: AsyncSession,
        filters: FilterT | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ModelT], int]:
        query = self.apply_filters(self.build_base_query(), filters)
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        count = int((await session.execute(count_query)).scalar_one())

        if self.list_order_by is not None:
            query = query.order_by(self.list_order_by)
        result = await session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), count

    async def create(
        self,
        *,
        session: AsyncSession,
        obj_in: CreateSchemaT,
        created_by: Any | None = None,
        **extra_fields: Any,
    ) -> ModelT:
        create_data = self.build_create_data(obj_in, **extra_fields)
        if self.audit_fields and created_by is not None and hasattr(self.model, "created_by"):
            create_data.setdefault("created_by", created_by)

        await self.before_create(session=session, obj_in=obj_in, create_data=create_data)
        db_obj = self.model(**create_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        await self.after_create(session=session, db_obj=db_obj, obj_in=obj_in)
        return db_obj

    async def update(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
        obj_in: UpdateSchemaT,
        updated_by: Any | None = None,
    ) -> ModelT:
        await self.before_update(session=session, db_obj=db_obj, obj_in=obj_in)
        self.apply_update_data(db_obj, obj_in)
        if self.audit_fields:
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.now(UTC)
            if updated_by is not None and hasattr(db_obj, "updated_by"):
                db_obj.updated_by = updated_by
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        await self.after_update(session=session, db_obj=db_obj, obj_in=obj_in)
        return db_obj

    async def delete(
        self,
        *,
        session: AsyncSession,
        db_obj: ModelT,
        deleted_by: Any | None = None,
    ) -> ModelT | None:
        await self.before_delete(session=session, db_obj=db_obj)
        if self.soft_delete and hasattr(db_obj, "deleted_at"):
            if hasattr(db_obj, "is_deleted"):
                db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now(UTC)
            if deleted_by is not None and hasattr(db_obj, "deleted_by"):
                db_obj.deleted_by = deleted_by
            session.add(db_obj)
            await session.commit()
            await self.after_delete(session=session, db_obj=db_obj)
            return db_obj

        await session.delete(db_obj)
        await session.commit()
        await self.after_delete(session=session, db_obj=db_obj)
        return None

    @property
    def can_export(self) -> bool:
        return bool(self.export_fields)

    async def get_all_for_export(
        self,
        *,
        session: AsyncSession,
        filters: FilterT | None = None,
    ) -> list[ModelT]:
        if not self.can_export:
            raise ValueError("CSV export is not enabled for this entity")

        query = self.apply_filters(self.build_base_query(), filters)
        if self.export_order_by is not None:
            query = query.order_by(self.export_order_by)
        result = await session.execute(query)
        return list(result.scalars().all())

    def serialize_export_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def serialize_export_row(self, db_obj: ModelT) -> dict[str, str]:
        return {
            field_name: self.serialize_export_value(getattr(db_obj, field_name, None))
            for field_name in self.export_fields
        }

    def export_to_csv(self, rows: list[ModelT]) -> str:
        if not self.can_export:
            raise ValueError("CSV export is not enabled for this entity")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.export_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(self.serialize_export_row(row))
        return output.getvalue()
