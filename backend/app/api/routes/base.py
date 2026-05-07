from collections.abc import Callable
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import SessionDep, permission_required
from app.crud.base import CRUDServiceBase
from app.models.user import User

CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)
PublicSchemaT = TypeVar("PublicSchemaT", bound=BaseModel)
ListSchemaT = TypeVar("ListSchemaT", bound=BaseModel)
FilterT = TypeVar("FilterT")
PKT = TypeVar("PKT")


class CRUDRouterBase(
    Generic[CreateSchemaT, UpdateSchemaT, PublicSchemaT, ListSchemaT, FilterT, PKT]
):
    prefix: str
    tag: str
    entity_name: str
    id_type: type[PKT]
    create_schema: type[CreateSchemaT]
    update_schema: type[UpdateSchemaT]
    public_schema: type[PublicSchemaT]
    list_schema: type[ListSchemaT]
    service: CRUDServiceBase[Any, CreateSchemaT, UpdateSchemaT, FilterT, PKT]
    permissions: dict[str, str]
    entity_label: str
    filter_dependency: Callable[..., FilterT] | None = None

    def get_route_summary(self, action: str) -> str:
        action_map = {
            "list": f"查询{self.entity_label}列表",
            "export": f"导出{self.entity_label}列表",
            "create": f"创建{self.entity_label}",
            "get": f"获取{self.entity_label}详情",
            "update": f"更新{self.entity_label}",
            "delete": f"删除{self.entity_label}",
        }
        return action_map[action]

    def get_route_description(self, action: str) -> str:
        action_map = {
            "list": f"按分页条件查询{self.entity_label}列表，并支持筛选参数。",
            "export": f"按当前筛选条件导出{self.entity_label} CSV 数据。",
            "create": f"创建一条新的{self.entity_label}记录。",
            "get": f"按主键读取单条{self.entity_label}详情。",
            "update": f"按主键更新一条{self.entity_label}记录。",
            "delete": f"按主键删除一条{self.entity_label}记录。",
        }
        return action_map[action]

    def to_public(self, db_obj: Any) -> PublicSchemaT:
        return self.public_schema.model_validate(db_obj, from_attributes=True)

    def to_list_response(self, items: list[Any], count: int) -> ListSchemaT:
        return self.list_schema(
            data=[self.to_public(item) for item in items],
            count=count,
        )

    def build_create_kwargs(
        self, *, current_user: User, body: CreateSchemaT
    ) -> dict[str, Any]:
        return {}

    def not_found_detail(self) -> str:
        return f"{self.entity_name} not found"

    def build_router(self) -> APIRouter:
        router = APIRouter(prefix=self.prefix, tags=[self.tag])
        create_schema = self.create_schema
        update_schema = self.update_schema
        public_schema = self.public_schema
        list_schema = self.list_schema
        id_type = self.id_type
        service = self.service
        permissions = self.permissions
        filter_dependency = type(self).filter_dependency

        if filter_dependency is None:

            @router.get(
                "/",
                response_model=list_schema,
                summary=self.get_route_summary("list"),
                description=self.get_route_description("list"),
            )
            async def list_entities_without_filters(
                session: SessionDep,
                _: User = Depends(permission_required(permissions["read"])),
                skip: int = 0,
                limit: int = 100,
            ) -> ListSchemaT:
                items, count = await service.get_multi(
                    session=session, filters=None, skip=skip, limit=limit
                )
                return self.to_list_response(items, count)

        else:

            @router.get(
                "/",
                response_model=list_schema,
                summary=self.get_route_summary("list"),
                description=self.get_route_description("list"),
            )
            async def list_entities_with_filters(
                session: SessionDep,
                _: User = Depends(permission_required(permissions["read"])),
                filters: Any = Depends(filter_dependency),
                skip: int = 0,
                limit: int = 100,
            ) -> ListSchemaT:
                items, count = await service.get_multi(
                    session=session, filters=filters, skip=skip, limit=limit
                )
                return self.to_list_response(items, count)

        if service.can_export and "export" in permissions:
            if filter_dependency is None:

                @router.get(
                    "/export/csv",
                    summary=self.get_route_summary("export"),
                    description=self.get_route_description("export"),
                )
                async def export_entities_csv_without_filters(
                    session: SessionDep,
                    _: User = Depends(permission_required(permissions["export"])),
                ) -> StreamingResponse:
                    rows = await service.get_all_for_export(session=session, filters=None)
                    csv_content = service.export_to_csv(rows)
                    return StreamingResponse(
                        iter([csv_content]),
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": (
                                f"attachment; filename={service.export_filename}"
                            )
                        },
                    )

            else:

                @router.get(
                    "/export/csv",
                    summary=self.get_route_summary("export"),
                    description=self.get_route_description("export"),
                )
                async def export_entities_csv_with_filters(
                    session: SessionDep,
                    _: User = Depends(permission_required(permissions["export"])),
                    filters: Any = Depends(filter_dependency),
                ) -> StreamingResponse:
                    rows = await service.get_all_for_export(
                        session=session, filters=filters
                    )
                    csv_content = service.export_to_csv(rows)
                    return StreamingResponse(
                        iter([csv_content]),
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": (
                                f"attachment; filename={service.export_filename}"
                            )
                        },
                    )

        @router.post(
            "/",
            response_model=public_schema,
            status_code=status.HTTP_201_CREATED,
            summary=self.get_route_summary("create"),
            description=self.get_route_description("create"),
        )
        async def create_entity(
            session: SessionDep,
            body: create_schema,  # type: ignore[valid-type]
            current_user: User = Depends(permission_required(permissions["create"])),
        ) -> PublicSchemaT:
            try:
                created = await service.create(
                    session=session,
                    obj_in=body,
                    created_by=current_user.id,
                    **self.build_create_kwargs(current_user=current_user, body=body),
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                )
            return self.to_public(created)

        @router.get(
            "/{obj_id}",
            response_model=public_schema,
            summary=self.get_route_summary("get"),
            description=self.get_route_description("get"),
        )
        async def get_entity(
            obj_id: id_type,  # type: ignore[valid-type]
            session: SessionDep,
            _: User = Depends(permission_required(permissions["read"])),
        ) -> PublicSchemaT:
            db_obj = await service.get_by_id(session=session, obj_id=obj_id)
            if not db_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=self.not_found_detail(),
                )
            return self.to_public(db_obj)

        @router.patch(
            "/{obj_id}",
            response_model=public_schema,
            summary=self.get_route_summary("update"),
            description=self.get_route_description("update"),
        )
        async def update_entity(
            obj_id: id_type,  # type: ignore[valid-type]
            session: SessionDep,
            body: update_schema,  # type: ignore[valid-type]
            current_user: User = Depends(permission_required(permissions["update"])),
        ) -> PublicSchemaT:
            db_obj = await service.get_by_id(session=session, obj_id=obj_id)
            if not db_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=self.not_found_detail(),
                )
            try:
                updated = await service.update(
                    session=session,
                    db_obj=db_obj,
                    obj_in=body,
                    updated_by=current_user.id,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                )
            return self.to_public(updated)

        @router.delete(
            "/{obj_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary=self.get_route_summary("delete"),
            description=self.get_route_description("delete"),
        )
        async def delete_entity(
            obj_id: id_type,  # type: ignore[valid-type]
            session: SessionDep,
            current_user: User = Depends(permission_required(permissions["delete"])),
        ) -> None:
            db_obj = await service.get_by_id(session=session, obj_id=obj_id)
            if not db_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=self.not_found_detail(),
                )
            try:
                await service.delete(
                    session=session,
                    db_obj=db_obj,
                    deleted_by=current_user.id,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                )

        return router
