# FastAPI Vue3 企业级模板

一个开箱即用的全栈企业级应用模板，基于 FastAPI + Vue3 + MySQL，包含完整的认证、权限、审计日志等企业级基础设施。

## 技术栈

### 后端
| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11 | 运行环境 |
| FastAPI | ≥0.114 | 异步 Web 框架 |
| SQLModel | ≥0.0.21 | ORM（基于 SQLAlchemy + Pydantic） |
| MySQL | 8.0 | 数据库 |
| aiomysql | ≥0.2.0 | 异步 MySQL 驱动 |
| Alembic | ≥1.12 | 数据库迁移 |
| pydantic-settings | ≥2.2 | 配置管理 |
| pyjwt | ≥2.8 | JWT 认证 |
| pwdlib[argon2,bcrypt] | — | 密码哈希（支持透明升级） |
| Sentry SDK | — | 错误追踪（生产可选） |

### 前端
| 组件 | 版本 | 说明 |
|------|------|------|
| Vue 3 | ^3.4 | 前端框架 |
| Vite | ^5.3 | 构建工具 |
| TypeScript | ~5.4 | 类型系统 |
| Element Plus | ^2.7 | UI 组件库 |
| Pinia | ^2.1 | 状态管理 |
| Vue Router | ^4.3 | 路由 |
| Axios | ^1.7 | HTTP 客户端 |

## 功能特性

### 认证与安全
- **双 Token 机制**：JWT Access Token（15分钟） + SHA-256 哈希的 Opaque Refresh Token（30天）
- **httpOnly Cookie**：Refresh Token 存储于 httpOnly Cookie，防止 XSS 窃取
- **Token 轮换**：每次刷新生成新的 Refresh Token，旧 Token 作废
- **密码哈希升级**：Bcrypt → Argon2 透明升级，无需用户操作
- **防时序攻击**：用户不存在时仍执行完整哈希验证

### RBAC 权限体系
- **三级权限树**：权限组（PermissionGroup）→ 权限页（PermissionPage）→ 权限点（Permission）
- **全码格式**：`{group}.{page}.{action}`，例如 `user_mgmt.users.read`
- **通配符匹配**：超级管理员拥有 `*` 权限，支持 fnmatch 匹配
- **导航数据驱动**：前端侧边栏根据用户权限动态渲染

### 软删除
所有业务表包含 `deleted_at` 字段，删除操作仅标记时间戳，不物理删除数据。

### 审计日志
`AuditLogMiddleware` 自动拦截所有非 GET 请求，记录：
- 请求/响应体（敏感字段自动脱敏，超过 10KB 自动截断）
- 状态码、耗时、IP、User-Agent
- 可选输出到 JSON Lines 文件（`LOG_TO_FILE=true`）

## 目录结构

```
fastapi-vue3-template/
├── .env.example              # 环境变量模板
├── compose.yml               # Docker Compose 编排
├── scripts/
│   ├── generate-env.sh       # 生成 .env 并随机化 SECRET_KEY
│   └── migrate.sh            # 在容器中运行 Alembic
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py           # FastAPI 应用入口
│       ├── backend_pre_start.py  # 数据库就绪检查
│       ├── initial_data.py   # 初始化数据（超管、权限树、角色）
│       ├── alembic/          # Alembic 迁移配置
│       ├── core/             # 配置、数据库引擎、安全工具
│       ├── models/           # SQLModel 数据模型
│       ├── schemas/          # Pydantic 请求/响应模型
│       ├── crud/             # 数据库操作层
│       ├── api/              # FastAPI 路由
│       └── middleware/       # 审计日志中间件
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── api/              # Axios API 封装
        ├── stores/           # Pinia 状态（auth、permission）
        ├── router/           # Vue Router（含权限守卫）
        ├── layouts/          # AdminLayout（动态侧边栏）
        └── views/            # 业务页面
```

## 快速开始

详见 [docs/quick-start.md](docs/quick-start.md)。

## 开发模式数据库说明

- 开发模式可直接连接你现有的 MySQL（无需 Docker 数据库）。
- 启动后端时会自动执行 `alembic upgrade head`，随后自动执行幂等初始化数据。
- 若当前没有任何 Alembic 迁移版本文件，启动时会自动按 SQLModel 元数据建表（仅用于本地开发初始化兜底）。
- 可通过环境变量关闭自动任务：
    - `AUTO_MIGRATE_ON_STARTUP=false`
    - `AUTO_SEED_ON_STARTUP=false`
    - `AUTO_CREATE_TABLES_IF_NO_MIGRATIONS=false`

## 默认凭证

| 字段 | 默认值 |
|------|--------|
| 用户名 | `admin` |
| 密码 | `changeme123` |

> **请在生产环境中立即修改默认密码！**

## API 文档

启动后访问：
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## License

MIT
