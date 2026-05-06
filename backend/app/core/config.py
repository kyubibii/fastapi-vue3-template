import secrets
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, HttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[3] / ".env"),
            str(Path(__file__).resolve().parents[2] / ".env"),
        ),
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(o).rstrip("/") for o in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "Enterprise FastAPI Template"
    SENTRY_DSN: HttpUrl | None = None
    AUTO_MIGRATE_ON_STARTUP: bool = True
    AUTO_SEED_ON_STARTUP: bool = True
    AUTO_CREATE_TABLES_IF_NO_MIGRATIONS: bool = True

    # ── MySQL ──────────────────────────────────────────────────────────────
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "app"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "appdb"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # ── First superuser ────────────────────────────────────────────────────
    FIRST_SUPERUSER: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@123456"

    # ── Email ──────────────────────────────────────────────────────────────
    SMTP_TLS: bool = False
    SMTP_SSL: bool = False
    SMTP_PORT: int = 1025
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    # ── Audit log ──────────────────────────────────────────────────────────
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "/var/log/app/audit.jsonl"

    # ── Runtime settings ──────────────────────────────────────────────────────
    SETTINGS_BOOTSTRAP_ENABLED: bool = True
    SETTINGS_BOOTSTRAP_ITEMS: list[dict[str, Any]] = [
        {
            "setting_name": "site_title",
            "setting_value": "Enterprise FastAPI Template",
            "setting_group": "display",
            "value_type": "string",
            "description": "后台系统标题",
        },
        {
            "setting_name": "dashboard_notice",
            "setting_value": "欢迎使用企业管理后台",
            "setting_group": "display",
            "value_type": "string",
            "description": "首页公告文案",
        },
        {
            "setting_name": "feature_user_register_enabled",
            "setting_value": "false",
            "setting_group": "feature",
            "value_type": "bool",
            "description": "是否允许用户自助注册",
        },
        {
            "setting_name": "smtp_host",
            "setting_value": "",
            "setting_group": "email",
            "value_type": "string",
            "description": "SMTP 主机地址",
        },
        {
            "setting_name": "smtp_port",
            "setting_value": "1025",
            "setting_group": "email",
            "value_type": "int",
            "description": "SMTP 端口",
        },
        {
            "setting_name": "smtp_password",
            "setting_value": "",
            "setting_group": "email",
            "value_type": "string",
            "description": "SMTP 密码",
            "is_sensitive": True,
            "is_encrypted": True,
        },
        {
            "setting_name": "access_token_expire_minutes",
            "setting_value": "15",
            "setting_group": "security",
            "value_type": "int",
            "description": "访问令牌过期分钟数",
        },
    ]
    RUNTIME_SETTINGS_CACHE_TTL_SECONDS: int = 60


settings = Settings()
