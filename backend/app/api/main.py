from fastapi import APIRouter

from app.api.routes import audit_logs, auth, items, permissions, roles, settings, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(audit_logs.router)
api_router.include_router(settings.router)
