from fastapi import APIRouter

from app.api.routes import (
	audit_logs,
	auth,
	dictionaries,
	items,
	jobs,
	permissions,
	roles,
	settings,
	users,
	wechat_pay,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
api_router.include_router(dictionaries.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(audit_logs.router)
api_router.include_router(settings.router)
api_router.include_router(jobs.router)
api_router.include_router(wechat_pay.router)
