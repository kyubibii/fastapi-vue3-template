# FastAPI Vue3 企业级全栈模板

一个**开箱即用**的全栈企业级应用模板，基于 **FastAPI + Vue3 + MySQL**，提供完整的身份认证、RBAC 权限、审计日志、定时任务等生产级基础设施。

## 📋 项目概览

### 核心能力

| 能力 | 说明 |
|------|------|
| **身份认证** | 双 Token JWT 机制（Access + Opaque Refresh Token）、密码升级透明化 |
| **权限管理** | 三级权限树 (Permission Group → Page → Action)、fnmatch 通配符匹配 |
| **审计追踪** | 自动中间件拦截、敏感字段脱敏、支持本地文件 / 数据库持久化 |
| **数据隔离** | 软删除（逻辑删除）、自动时间戳管理 |
| **定时任务** | APScheduler 内置支持（Cron、Interval、Date） |
| **数据库演进** | Alembic 版本管理、自动启动迁移、初始数据幂等注入 |
| **前端权限** | Vue Router 守卫 + 权限驱动的导航菜单 |
| **开发友好** | 无 Docker 本地开发、热重载、自动初始化 |

---

## 🛠️ 技术栈详解

### 后端技术栈

#### 核心框架
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| Python | 3.11+ | 编程语言 | 高性能异步运行时 |
| FastAPI | ≥0.114 | Web 框架 | 异步 API、自动文档、性能优先 |
| Uvicorn | ✓ | ASGI 服务器 | 高性能异步 HTTP 服务器 |

#### 数据层
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| SQLModel | ≥0.0.21 | ORM | SQLAlchemy + Pydantic 结合，既用做 ORM 也用做 Schema |
| SQLAlchemy | ✓ (via SQLModel) | 数据库抽象 | 数据库无关性、关系管理 |
| aiomysql | ≥0.2.0 | MySQL 驱动 | 完全异步的 MySQL 连接 |
| MySQL | 8.0 | 关系数据库 | 数据持久化 |
| Alembic | ≥1.12 | 数据库迁移 | 版本管理、自动升级、回滚能力 |

#### 安全认证
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| PyJWT | ≥2.8 | JWT 库 | Access Token 编码/解码 |
| pwdlib[argon2,bcrypt] | ≥0.3.0 | 密码库 | 双哈希算法支持、透明升级 |
| secrets | ✓ (stdlib) | 安全生成 | Opaque Refresh Token 生成 |

#### 配置与日志
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| pydantic-settings | ≥2.2 | 配置管理 | 环境变量强类型、嵌套配置 |
| Sentry SDK | ≥2.0.0 | 错误追踪 | 生产环境异常捕获（可选） |

#### 定时与异步
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| APScheduler | ≥3.10 | 定时任务框架 | Cron、Interval、One-off 任务 |
| tenacity | ≥8.2 | 重试库 | 指数退避重试策略 |

#### 开发工具
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| pytest | ≥8.0.0 | 测试框架 | 单元测试、集成测试 |
| pytest-asyncio | ≥0.23.0 | 异步测试 | 支持 async/await 测试 |
| mypy | ≥1.8.0 | 类型检查 | 静态类型分析（strict mode） |
| ruff | ≥0.2.2 | 代码检查 | 快速 Linter + Formatter |

---

### 前端技术栈

#### 核心框架
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| Vue 3 | ^3.4 | 前端框架 | 组件化开发、响应式系统 |
| Vite | ^5.3 | 构建工具 | 极速开发服务器、编译优化 |
| TypeScript | ~5.4 | 类型系统 | 前端类型安全、IDE 支持 |

#### UI 与样式
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| Element Plus | ^2.7 | UI 组件库 | 企业级组件、表格、表单、弹窗 |
| @element-plus/icons-vue | ^2.3 | 图标库 | SVG 图标库 |

#### 状态与路由
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| Pinia | ^2.1 | 状态管理 | 替代 Vuex，轻量高效 |
| Vue Router | ^4.3 | 路由框架 | SPA 路由、权限守卫 |

#### HTTP 通信
| 组件 | 版本 | 说明 | 用途 |
|------|------|------|------|
| Axios | ^1.7 | HTTP 客户端 | REST API 请求、拦截器 |

---

## 🐳 基础设施与部署

### Docker Compose 编排

项目使用 **Docker Compose** 协调多个服务，完整容器栈包括：

```yaml
服务拓扑图：
┌──────────────┐
│   Frontend   │ (Vue3 + Nginx, 端口 80)
│  (nginx:*)   │
└──────┬───────┘
       │ 反向代理 /api → backend:8000
       ↓
┌──────────────────┐
│    Backend       │ (FastAPI, 端口 8000)
│   (uvicorn)      │
└──────┬───────────┘
       │ 连接
       ↓
┌──────────────────┐
│      MySQL       │ (端口 3306)
│       8.0        │
└──────────────────┘

可选服务：
┌──────────────────┐
│     MailHog      │ (SMTP: 1025, UI: 8025)
│   (邮件沙箱)     │
└──────────────────┘
```

#### 服务说明

| 服务 | 镜像 | 端口 | 用途 | 健康检查 |
|------|------|------|------|---------|
| **db** | mysql:8.0 | 3306 | 数据库 | mysqladmin ping |
| **backend** | Dockerfile (./backend) | 8000 | FastAPI API | ✗ |
| **frontend** | Dockerfile (./frontend) | 80 | Vue3 Web 应用 | ✗ |
| **mailhog** | mailhog/mailhog | 1025, 8025 | 开发邮件沙箱 | ✗ |

#### 网络隔离
- 所有服务共享默认 bridge 网络
- 容器间通过 `service_name:port` 直接通信（无需 localhost）
- 后端配置：`MYSQL_SERVER=db` 而非 `localhost`
- 前端 Nginx 反向代理：`/api/*` 转发至 `http://backend:8000/api/*`

#### 数据持久化
```yaml
volumes:
  mysql_data:           # Docker 管理卷，自动在 host 创建
    driver: local
```
MySQL 数据存储在 Docker Volume，**重启后数据保留**。

#### 依赖关系
```yaml
dependencies:
  backend:
    depends_on:
      db:
        condition: service_healthy  # 等待 DB 健康才启动 backend
  frontend:
    depends_on:
      - backend                      # 弱依赖，仅保证启动顺序
```

---

### 环境变量配置

详见 [.env.example](.env.example)，核心配置分类：

#### 应用配置
```env
APP_ENV=development                              # 运行环境
PROJECT_NAME="Enterprise FastAPI Template"      # 项目名称
SECRET_KEY=<随机字符串>                         # JWT 密钥（生成脚本自动处理）
ACCESS_TOKEN_EXPIRE_MINUTES=15                 # Access Token 有效期
REFRESH_TOKEN_EXPIRE_DAYS=30                   # Refresh Token 有效期
```

#### 数据库配置
```env
MYSQL_SERVER=db                    # 容器环境下为 service 名称
MYSQL_PORT=3306
MYSQL_USER=app
MYSQL_PASSWORD=changeme            # ⚠️ 改为强密码
MYSQL_DB=appdb
```

#### 初始数据
```env
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=Admin@123456  # ⚠️ 必须修改
```

#### CORS 配置
```env
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:80"]
FRONTEND_HOST=http://localhost:5173
```

#### 邮件配置
```env
SMTP_HOST=mailhog        # 本地开发使用 MailHog
SMTP_PORT=1025
SMTP_TLS=false
SMTP_SSL=false
EMAILS_FROM_EMAIL=noreply@example.com
```

#### 审计日志配置
```env
LOG_TO_FILE=false                           # 启用文件持久化
LOG_FILE_PATH=/var/log/app/audit.jsonl     # 审计日志路径
```

#### 错误追踪（生产可选）
```env
SENTRY_DSN=<your-sentry-dsn>
ENVIRONMENT=development
```

#### 启动自动化
```env
AUTO_MIGRATE_ON_STARTUP=true          # 自动执行 Alembic 升级
AUTO_SEED_ON_STARTUP=true             # 自动注入初始数据
AUTO_CREATE_TABLES_IF_NO_MIGRATIONS=true  # 无迁移文件时使用 SQLModel 元数据建表
```

---

## 📂 目录结构详解

```
fastapi-vue3-template/
│
├── 📄 compose.yml                    ← Docker Compose 编排文件（核心）
├── 📄 .env.example                   ← 环境变量模板
├── 📄 README.md                      ← 本文件
├── 📄 pyproject.toml                 ← 项目元数据（前端）
│
├── 📁 scripts/                       ← 辅助脚本
│   ├── generate-env.sh              ← 生成 .env（自动化 SECRET_KEY）
│   └── migrate.sh                   ← 容器内数据库迁移脚本
│
├── 📁 docs/
│   ├── quick-start.md               ← 快速开始指南（必读）
│   └── ...
│
├── 📁 backend/                       ← FastAPI 后端
│   ├── 📄 Dockerfile                 ← 多阶段构建（依赖 → 运行）
│   ├── 📄 pyproject.toml             ← Python 依赖定义（uv 工具）
│   ├── 📄 alembic.ini                ← Alembic 配置
│   │
│   └── 📁 app/                       ← 应用源代码
│       ├── main.py                  ← FastAPI 应用入口
│       │                             ├─ 启动事件（迁移、初始化、定时任务）
│       │                             ├─ CORS 中间件
│       │                             ├─ 审计日志中间件
│       │                             └─ API 路由注册
│       │
│       ├── backend_pre_start.py      ← 启动前检查（数据库连接）
│       ├── initial_data.py           ← 初始化脚本（超管、权限树、角色）
│       │
│       ├── 📁 alembic/               ← 数据库迁移
│       │   ├── env.py                ← 迁移环境配置
│       │   ├── script.py.mako        ← 迁移模板
│       │   └── versions/             ← 迁移历史版本
│       │       ├── 20260506_01_*.py  ← 迁移脚本（自动编号）
│       │       └── ...
│       │
│       ├── 📁 core/                  ← 核心配置模块
│       │   ├── config.py             ← Pydantic Settings（环境变量读取）
│       │   ├── db.py                 ← 数据库连接（async engine）
│       │   ├── runtime_settings.py   ← 运行时设置（从数据库读取）
│       │   └── security.py           ← JWT、密码、Token 工具函数
│       │
│       ├── 📁 models/                ← SQLModel 数据模型（数据库表）
│       │   ├── __init__.py           ← 导出所有模型
│       │   ├── base.py               ← 基础模型（id、创建时间等）
│       │   ├── user.py               ← 用户、角色、权限模型
│       │   ├── rbac.py               ← RBAC 权限树模型
│       │   ├── item.py               ← 业务模型示例
│       │   ├── audit_log.py          ← 审计日志模型
│       │   └── ...
│       │
│       ├── 📁 schemas/               ← Pydantic 请求/响应模型
│       │   ├── user.py               ← 用户相关 schema
│       │   ├── auth.py               ← 认证相关 schema
│       │   ├── rbac.py               ← 权限相关 schema
│       │   └── ...
│       │
│       ├── 📁 crud/                  ← CRUD 操作层（数据库访问）
│       │   ├── base.py               ← 通用 CRUD 基类（Create Read Update Delete）
│       │   ├── user.py               ← 用户 CRUD
│       │   ├── permissions.py        ← 权限 CRUD
│       │   └── ...
│       │
│       ├── 📁 api/                   ← FastAPI 路由（API 端点）
│       │   ├── main.py               ← 路由总入口（所有 router 注册）
│       │   ├── deps.py               ← 依赖注入（认证、权限检查）
│       │   └── routes/               ← 按功能划分的路由组
│       │       ├── auth.py           ← 认证接口（登录、刷新）
│       │       ├── users.py          ← 用户管理接口
│       │       ├── permissions.py    ← 权限接口
│       │       ├── roles.py          ← 角色接口
│       │       ├── items.py          ← 业务数据接口（示例）
│       │       ├── audit_logs.py     ← 审计日志接口
│       │       ├── jobs.py           ← 定时任务管理接口
│       │       ├── settings.py       ← 系统设置接口
│       │       └── ...
│       │
│       ├── 📁 middleware/            ← 中间件
│       │   └── audit_log.py          ← 审计日志中间件
│       │                             ├─ 自动拦截所有非 GET 请求
│       │                             ├─ 敏感字段脱敏
│       │                             ├─ 请求/响应体截断
│       │                             └─ 数据库 / 文件持久化
│       │
│       ├── 📁 jobs/                  ← 定时任务
│       │   ├── scheduler.py          ← APScheduler 调度器
│       │   ├── registry.py           ← 任务注册表
│       │   └── definitions/          ← 任务定义
│       │       ├── example_cron.py   ← Cron 示例（如：每日 00:00 运行）
│       │       ├── example_interval.py ← 间隔示例（如：每 5 分钟）
│       │       └── example_date.py   ← 一次性示例（如：指定时间运行）
│       │
│       └── logs/                     ← 应用日志目录（可选）
│           └── audit.jsonl           ← 审计日志文件（LOG_TO_FILE=true 时）
│
└── 📁 frontend/                      ← Vue3 前端
    ├── 📄 Dockerfile                 ← 多阶段构建（构建 → Nginx 运行）
    ├── 📄 nginx.conf                 ← Nginx 配置
    │                                 ├─ 反向代理：/api/* → backend:8000
    │                                 ├─ SPA 路由：404 → index.html
    │                                 └─ 缓存策略
    ├── 📄 package.json               ← npm 依赖定义
    ├── 📄 pnpm-lock.yaml             ← 依赖锁文件
    ├── 📄 index.html                 ← HTML 入口
    ├── 📄 tsconfig.json              ← TypeScript 配置
    ├── 📄 vite.config.ts             ← Vite 构建配置
    │
    └── 📁 src/                       ← 源代码
        ├── main.ts                  ← 应用入口（Vue 实例初始化）
        ├── App.vue                  ← 根组件
        │
        ├── 📁 api/                   ← Axios 封装（API 客户端）
        │   ├── index.ts              ← Axios 实例、拦截器（自动注入 token）
        │   ├── users.ts              ← 用户相关 API
        │   ├── items.ts              ← 业务数据 API
        │   ├── rbac.ts               ← 权限相关 API
        │   ├── audit-logs.ts         ← 审计日志 API
        │   └── ...
        │
        ├── 📁 stores/                ← Pinia 状态管理
        │   ├── auth.ts               ← 认证状态（当前用户、token）
        │   ├── permission.ts         ← 权限状态（当前用户权限列表）
        │   └── ...
        │
        ├── 📁 router/                ← Vue Router 配置
        │   ├── index.ts              ← 路由总入口、权限守卫
        │   └── modules/              ← 按功能划分的路由模块
        │       ├── auth.ts           ← 认证相关路由（登录、登出）
        │       ├── dashboard.ts      ← 仪表板路由
        │       ├── users.ts          ← 用户管理路由
        │       ├── items.ts          ← 业务数据路由
        │       ├── system.ts         ← 系统设置路由
        │       └── ...
        │
        ├── 📁 layouts/               ← 布局组件
        │   └── AdminLayout.vue       ← 管理后台布局
        │                             ├─ 侧边栏（权限驱动）
        │                             ├─ 顶部栏（用户菜单）
        │                             └─ 主内容区
        │
        └── 📁 views/                 ← 页面组件
            ├── 📁 auth/
            │   └── LoginView.vue     ← 登录页
            ├── 📁 dashboard/
            │   └── WelcomeView.vue   ← 欢迎页
            ├── 📁 items/             ← 业务数据页面
            │   ├── ItemListView.vue  ← 列表（CRUD 示例）
            │   └── ItemFormView.vue  ← 表单（新增/编辑）
            ├── 📁 users/             ← 用户管理
            │   └── ...
            ├── 📁 system/            ← 系统设置
            │   ├── RolePermissionView.vue  ← 角色权限配置
            │   ├── AuditLogListView.vue    ← 审计日志查询
            │   ├── JobManagementView.vue   ← 定时任务管理
            │   └── ...
            └── 📁 common/
                ├── ForbiddenView.vue ← 403 无权限页
                └── ...
```

---

## 🚀 快速开始

详见 [docs/quick-start.md](docs/quick-start.md)。

## 💾 开发模式数据库说明

### 无 Docker 本地开发

开发模式支持**直接连接现有 MySQL**（无需 Docker 数据库）：

1. **启动后端时自动化**：
   - 执行 `alembic upgrade head`（应用所有迁移）
   - 执行幂等初始化数据（超管、权限树、角色）

2. **迁移文件引导**：
   - 若存在 Alembic 迁移版本文件 → 使用迁移
   - 若不存在 → 使用 SQLModel 元数据直接建表（仅兜底）

3. **关闭自动化**：
   ```env
   AUTO_MIGRATE_ON_STARTUP=false      # 跳过迁移
   AUTO_SEED_ON_STARTUP=false         # 跳过初始化
   ```

### 容器化部署

Docker Compose 管理完整栈：
- 自动构建、启动、健康检查
- 数据库卷持久化
- 网络隔离与服务发现
- 一条命令启动全部服务

---

## 🔗 文档导航

### 📖 用户文档

| 文档 | 目的 | 适合人群 |
|------|------|---------|
| [快速开始](docs/quick-start.md) | 5 分钟启动项目 | 初次使用者 |
| [开发指南](docs/development.md) | 本地开发工作流 | 后端/前端开发者 |
| [架构设计](docs/architecture.md) | 系统架构与 API 设计 | 技术负责人、架构师 |
| [部署指南](docs/deployment.md) | 生产环境部署 | 运维工程师 |

### 📚 API 文档

项目运行后，在浏览器访问：
- **Swagger UI**：http://localhost:8000/api/v1/docs
- **ReDoc**：http://localhost:8000/api/v1/redoc

### 💻 在线开发环境

- **前端开发服务器**：http://localhost:5173（无 Docker 本地开发）
- **后端 API 服务器**：http://localhost:8000（无 Docker 本地开发）
- **MailHog 邮件 UI**：http://localhost:8025（容器化部署）

---

## 🤝 贡献指南

欢迎 PR 和 Issue！请：

1. **遵循代码规范**
   ```bash
   # 后端
   cd backend && ruff check app && mypy app
   
   # 前端
   cd frontend && pnpm run lint
   ```

2. **编写测试**
   ```bash
   cd backend && pytest
   ```

3. **更新文档**
   - 修改功能时同步更新对应文档
   - 添加新 API 时在 Swagger 中注释

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## ❓ 常见问题

### Q：项目可以用于商业用途吗？

A：可以。MIT 许可证允许商业使用，仅需保留许可证声明。

### Q：如何获取更新？

A：

```bash
git remote add upstream https://github.com/kyubibii/fastapi-vue3-template.git
git fetch upstream
git merge upstream/main
```

### Q：遇到问题怎么办？

A：按优先级：
1. 检查 [quick-start.md](docs/quick-start.md) 故障排查章节
2. 查看 [development.md](docs/development.md) 开发常见问题
3. 在 GitHub Issues 搜索相似问题
4. 提交新 Issue 附带错误日志、环境信息

---

## 📊 项目统计

| 指标 | 值 |
|------|-----|
| 后端代码行数 | ~2000+ |
| 前端代码行数 | ~1500+ |
| 测试覆盖率 | 待补充 |
| 文档页数 | 6 页（本 README + 5 个 .md 文件） |
| 支持的 Python 版本 | 3.11+ |
| 支持的 Node.js 版本 | 18+ |

---

## 🎯 项目路线图

### 已完成 ✅
- [x] 双 Token JWT 认证
- [x] 三级 RBAC 权限树
- [x] 审计日志中间件
- [x] 软删除设计
- [x] Alembic 数据库迁移
- [x] APScheduler 定时任务
- [x] Docker Compose 容器编排
- [x] Vue3 + Element Plus 管理界面
- [x] 权限驱动的前端导航
- [x] Axios 请求拦截器
- [x] 完整开发文档

### 计划中 📋
- [ ] 单元测试框架集成
- [ ] 集成测试（TestContainers）
- [ ] 国际化（i18n）支持
- [ ] 黑暗主题
- [ ] 消息队列集成（RabbitMQ / Redis）
- [ ] 全文搜索（Elasticsearch）
- [ ] 多租户支持
- [ ] Kubernetes 部署配置
- [ ] GraphQL API（可选）

### 待评估 🔄
- OpenAI API 集成示例
- 移动应用（React Native / Flutter）
- 微服务架构演进指南
- 性能基准测试

---

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL + ORM + Pydantic
- [Vue 3](https://vuejs.org/) - 渐进式前端框架
- [Element Plus](https://element-plus.org/) - 企业级 UI 组件库
- [Alembic](https://alembic.sqlalchemy.org/) - 数据库迁移工具
- [APScheduler](https://apscheduler.readthedocs.io/) - 定时任务调度器

---

**最后更新**：2026 年 5 月 6 日
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
