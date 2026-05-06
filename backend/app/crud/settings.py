from typing import Any, cast

from app.crud.base import CRUDServiceBase
from app.models.setting import Setting
from app.schemas.setting import (
    SettingCreate,
    SettingListFilter,
    SettingUpdate,
    validate_setting_value,
)


class SettingCRUDService(
    CRUDServiceBase[Setting, SettingCreate, SettingUpdate, SettingListFilter, int]
):
    model = Setting
    list_order_by = cast(Any, Setting.created_at).desc()

    def apply_filters(self, query: Any, filters: SettingListFilter | None) -> Any:
        if not filters:
            return query
        if filters.setting_group:
            query = query.where(
                Setting.setting_group == filters.setting_group.strip().lower()
            )
        if filters.setting_name:
            query = query.where(
                cast(Any, Setting.setting_name).contains(filters.setting_name.strip().lower())
            )
        if filters.is_sensitive is not None:
            query = query.where(Setting.is_sensitive == filters.is_sensitive)
        return query

    async def before_create(
        self,
        *,
        session: Any,
        obj_in: SettingCreate,
        create_data: dict[str, Any],
    ) -> None:
        create_data["setting_name"] = create_data["setting_name"].strip().lower()
        create_data["setting_group"] = create_data["setting_group"].strip().lower()
        create_data["value_type"] = create_data["value_type"].strip().lower()
        validate_setting_value(create_data.get("setting_value"), create_data["value_type"])

    async def before_update(
        self,
        *,
        session: Any,
        db_obj: Setting,
        obj_in: SettingUpdate,
    ) -> None:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return

        if db_obj.is_readonly:
            raise ValueError("This setting is readonly")

        if "setting_group" in update_data and update_data["setting_group"] is not None:
            update_data["setting_group"] = update_data["setting_group"].strip().lower()
            obj_in.setting_group = update_data["setting_group"]

        target_type = cast(str, update_data.get("value_type", db_obj.value_type))
        if "setting_value" in update_data:
            validate_setting_value(cast(str | None, update_data.get("setting_value")), target_type)
        elif "value_type" in update_data:
            validate_setting_value(db_obj.setting_value, target_type)


service = SettingCRUDService()