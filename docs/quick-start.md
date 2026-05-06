# 快速开始指南

本文档帮助你用 **5 分钟** 将项目跑起来，支持两种方式：容器化部署和本地开发。

---

## 📋 前置条件

### 容器化部署（推荐初次体验）
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- [Git](https://git-scm.com/) 已安装
- 可用磁盘空间：≥ 2GB（镜像 + 数据库）
- 可用端口：80（前端）、8000（后端 API）、3306（MySQL）、8025（MailHog UI）

### 本地开发（无 Docker）
- Python 3.11+
- Node.js 18+ 和 pnpm
- MySQL 8.0+ 本地实例
- Git 已安装

---

## 方案 A：容器化部署（Docker Compose）

最简单的方式，一条命令启动完整的应用栈。

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-org/fastapi-vue3-template.git
cd fastapi-vue3-template
```

### 步骤 2：生成环境配置

```bash
# Linux / macOS
bash scripts/generate-env.sh
```

**Windows PowerShell：**
```powershell
Copy-Item .env.example .env
# 然后手动编辑 .env，用强随机字符串替换 SECRET_KEY
# 例如：openssl rand -hex 32
```

生成的 `.env` 文件内容示例：
```env
APP_ENV=development
PROJECT_NAME="Enterprise FastAPI Template"
SECRET_KEY=a9f3c8d7e2b1f4a6c9e3d8a1b5f2c7e9a4d1b8c5f9e2a3d6c9f1e4b7a2d5c8e  # 自动生成
...
```

### 步骤 3：（可选）自定义环境变量

编辑 `.env` 文件，根据需要修改关键配置：

```env
# 数据库密码（建议改为强密码）
MYSQL_PASSWORD=YourStrongPassword123!

# 初始超管凭证（⚠️ 生产必须修改！）
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=changeme123

# SMTP 配置（开发环境使用 MailHog）
SMTP_HOST=mailhog
SMTP_PORT=1025

# 审计日志配置
LOG_TO_FILE=true              # 启用文件持久化
LOG_FILE_PATH=/app/logs/audit.jsonl
```

完整参数说明见 [项目根目录 .env.example](.env.example)。

### 步骤 4：启动所有服务

```bash
docker compose up -d
```

首次启动（约 3-5 分钟）：
```
Creating network "fastapi-vue3-template_default" ...
Building backend image...
  ✓ Layer 1: Python 3.11 base
  ✓ Layer 2: Dependencies (deps)
  ✓ Layer 3: Application (app)
  => Build complete: 2m14s
Building frontend image...
  ✓ Layer 1: Node 18 base
  ✓ Layer 2: Dependencies
  ✓ Layer 3: Build dist
  ✓ Layer 4: Nginx runtime
  => Build complete: 1m43s
Starting containers...
  ✓ db (healthy in 15s)
  ✓ backend (running in 8s)
    - AutoMigrate: ✓ Alembic upgraded
    - AutoSeed: ✓ Initial data injected
    - Jobs: ✓ Scheduler started
  ✓ frontend (running in 5s)
  ✓ mailhog (running in 3s)
```

### 步骤 5：验证服务健康

```bash
docker compose ps
```

所有服务应显示 `healthy` 或 `running`：
```
NAME         STATUS              PORTS
fastapi-vue3-template-backend-1   running   0.0.0.0:8000->8000/tcp
fastapi-vue3-template-frontend-1  running   0.0.0.0:80->80/tcp
fastapi-vue3-template-db-1        running   0.0.0.0:3306->3306/tcp
fastapi-vue3-template-mailhog-1   running   0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
```

若任何服务异常，查看日志：
```bash
docker compose logs backend    # 后端日志
docker compose logs frontend   # 前端日志
docker compose logs db         # 数据库日志
```

### 步骤 6：访问应用

| 服务 | 地址 | 说明 |
|------|------|------|
| **管理后台** | http://localhost | Vue3 Web 界面 |
| **API 文档** | http://localhost:8000/api/v1/docs | Swagger UI（可在线测试） |
| **邮件沙箱** | http://localhost:8025 | MailHog Web UI（开发邮件） |

### 步骤 7：登录

使用 `.env` 中定义的凭证：

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `changeme123` |

### 常见操作

#### 停止所有服务
```bash
docker compose down
```

#### 清除数据（重新初始化）
```bash
docker compose down -v        # -v 删除数据卷
docker compose up -d
```

#### 查看实时日志
```bash
docker compose logs -f backend
```

#### 重启单个服务
```bash
docker compose restart backend
```

---

## 方案 B：本地开发（无 Docker）

用于主开发工作流，支持热重载、快速迭代。

### 前置要求

- **Python 3.11+**
  ```bash
  python --version
  # Python 3.11.x 或更高版本
  ```

- **Node.js + pnpm**
  ```bash
  node --version       # v18+
  npm install -g pnpm  # 全局安装 pnpm
  pnpm --version       # v8+
  ```

- **MySQL 8.0+（本地运行）**
  ```bash
  mysql --version      # Ver 8.0.x
  
  # 确保 MySQL 服务运行
  # macOS: brew services start mysql
  # Windows: 在 Services 中启动 MySQL 服务
  # Linux: systemctl start mysql
  ```

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-org/fastapi-vue3-template.git
cd fastapi-vue3-template
```

### 步骤 2：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，指向本地 MySQL：

```env
MYSQL_SERVER=localhost    # 或 127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root           # 或你的 MySQL 用户
MYSQL_PASSWORD=your_password
MYSQL_DB=appdb
```

验证 MySQL 连接：
```bash
mysql -h localhost -u root -p
# 输入密码，若成功进入 mysql> 提示符，说明 MySQL 就绪
```

### 步骤 3：启动后端

#### 创建虚拟环境

```bash
cd backend

# 创建虚拟环境
uv venv
# 或：python -m venv .venv

# 激活虚拟环境
# Windows PowerShell：
.\.venv\Scripts\Activate.ps1

# Windows CMD：
.\.venv\Scripts\activate.bat

# Linux / macOS：
source .venv/bin/activate
```

#### 安装依赖

```bash
# 使用 uv（更快）
uv pip install -e .

# 或使用 pip
pip install -e .

# 验证安装
python -c "import fastapi; print(fastapi.__version__)"
```

#### 启动开发服务器

```bash
# 自动迁移 + 初始化 + 启动
uvicorn app.main:app --reload --port 8000
```

输出示例：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:     Running alembic migrations...
INFO:     Alembic migrations completed.
INFO:     Seeding initial data...
INFO:     Initial data seeded.
INFO:     Scheduler started.
```

后端已就绪！访问 http://localhost:8000/api/v1/docs 查看 API 文档。

### 步骤 4：启动前端

#### 新建终端窗口

```bash
cd frontend
```

#### 安装依赖

```bash
pnpm install
```

首次安装约 1-2 分钟（下载 npm 包）。

#### 启动开发服务器

```bash
pnpm dev
```

输出示例：
```
  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

访问 http://localhost:5173 查看前端界面。

### 步骤 5：登录应用

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `Admin@123456` |

### 开发工作流

#### 后端开发

```bash
cd backend

# 自动热重载（修改代码后自动刷新）
uvicorn app.main:app --reload

# 运行类型检查
mypy app

# 运行代码检查
ruff check app

# 运行自动格式化
ruff format app
```

#### 前端开发

```bash
cd frontend

# 开发服务器（热重载）
pnpm dev

# 类型检查
pnpm run check     # vue-tsc --noEmit

# 代码检查和修复
pnpm run lint

# 构建生产包
pnpm build
```

#### 数据库迁移

创建新迁移（修改 SQLModel 模型后）：

```bash
cd backend

# 自动生成迁移（对比当前模型与最后迁移）
alembic revision --autogenerate -m "add new column"

# 应用迁移
alembic upgrade head

# 回滚最后一个迁移
alembic downgrade -1
```

---

## 🔧 故障排查

### 容器化部署

#### 问题：`docker compose up` 后 backend 一直在重启

**症状：** Backend 日志显示数据库连接失败

**解决：**
```bash
# 查看完整日志
docker compose logs backend

# 检查数据库是否健康
docker compose ps db

# 手动检查数据库连接
docker compose exec db mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"
```

#### 问题：端口已被占用

**症状：** `Error: bind: address already in use`

**解决：**
```bash
# 查看占用的端口
lsof -i :80      # 前端
lsof -i :8000    # 后端
lsof -i :3306    # 数据库

# 杀死进程或修改 compose.yml 中的端口
docker compose down
# 编辑 compose.yml，改为其他端口
docker compose up -d
```

### 本地开发

#### 问题：MySQL 连接失败

**症状：** `pymysql.Error: (2003, "Can't connect to MySQL server")`

**解决：**
```bash
# 检查 MySQL 服务是否运行
mysql -h localhost -u root -p

# 验证 .env 配置
cat .env | grep MYSQL

# 重启 MySQL（示例）
# macOS: brew services restart mysql
# Windows: 在 Services 中重启 MySQL
```

#### 问题：后端启动时迁移失败

**症状：** `alembic: error: can't find package python`

**解决：**
```bash
# 确保虚拟环境激活
which python  # 或 where python（Windows）
# 输出应该包含 .venv 路径

# 重装依赖
pip install -e .
```

#### 问题：前端热重载不工作

**症状：** 修改代码后页面不更新

**解决：**
```bash
# 清除 node_modules 和 vite 缓存
rm -rf node_modules .pnpm-store
pnpm install

# 重启开发服务器
pnpm dev
```

---

## 📚 下一步

- **API 调用**：查看 [API 文档](http://localhost:8000/api/v1/docs)
- **代码库文件说明**：见项目 README.md 中的目录结构章节
- **权限管理**：管理后台 → 系统 → 角色权限，配置应用权限体系
- **定时任务**：管理后台 → 系统 → 任务管理，查看和配置定时任务
- **审计日志**：管理后台 → 系统 → 审计日志，追踪所有数据变更

---

## 💡 常见问题

### Q1：我想在生产环境部署，需要做什么？

A：见项目文档 `docs/deployment.md`（待补充）。核心步骤：
1. 修改 `.env` 的所有敏感配置（SECRET_KEY、MYSQL_PASSWORD、初始密码）
2. 启用 HTTPS（通过 Nginx 反向代理 + Let's Encrypt）
3. 启用 Sentry 错误追踪（生产可选）
4. 使用外部 MySQL（RDS / 云数据库）
5. 使用生产级 SMTP（SendGrid / AWS SES）
6. 配置备份策略

### Q2：如何添加新的数据模型？

A：见项目文档 `docs/development.md`（待补充）。简要步骤：
1. 在 `backend/app/models/` 中定义 SQLModel 类
2. 在 `backend/app/schemas/` 中定义请求/响应 Pydantic 类
3. 在 `backend/app/crud/` 中实现 CRUD 操作
4. 在 `backend/app/api/routes/` 中定义路由
5. 运行 `alembic revision --autogenerate -m "add xxx table"` 生成迁移
6. 在前端对应位置实现 UI

### Q3：如何修改密码哈希算法（Bcrypt → Argon2）？

A：已内置支持透明升级。修改 `backend/app/core/security.py` 中的 `password_hash` 定义：

```python
# 当前配置：优先使用 Argon2，兼容旧 Bcrypt 密码
password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))

# 用户下次登录时会自动升级到 Argon2
```

### Q4：如何关闭审计日志？

A：在 `.env` 中禁用中间件：

```env
# 方案 1：关闭审计日志中间件（在 app/main.py 中注释）
# 方案 2：仅关闭文件持久化
LOG_TO_FILE=false
```

---

## 🆘 获取帮助

- **查看项目日志**：`docker compose logs -f service_name`
- **查看 API 文档**：http://localhost:8000/api/v1/docs
- **查看代码注释**：源代码文件包含详细的中文注释
- **GitHub Issues**：在项目 issue 中提出问题

> 自动启动任务说明：
> - `AUTO_MIGRATE_ON_STARTUP=true`：应用启动时自动迁移到最新版本
> - `AUTO_SEED_ON_STARTUP=true`：应用启动时自动执行幂等初始化数据
> - `AUTO_CREATE_TABLES_IF_NO_MIGRATIONS=true`：若无 Alembic 版本文件，按 SQLModel 元数据自动建表
>
> 如需关闭，可在 `.env` 中设置：
> ```env
> AUTO_MIGRATE_ON_STARTUP=false
> AUTO_SEED_ON_STARTUP=false
> AUTO_CREATE_TABLES_IF_NO_MIGRATIONS=false
> ```

### 前端（无 Docker）

```bash
cd frontend

# 安装依赖（推荐 pnpm）
npm install -g pnpm
pnpm install

# 启动开发服务器（代理 /api 到 localhost:8000）
pnpm dev
```

如需改代理目标（例如后端运行在 8011，避免与其他项目冲突），在 [frontend/.env.development](frontend/.env.development) 设置：

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8011
```

访问 http://localhost:5173

### 单端口运行（后端直接挂载前端构建产物）

```bash
cd frontend
pnpm build

cd ../backend
uv run fastapi dev app/main.py --host 127.0.0.1 --port 8000
```

构建完成后，后端会自动挂载 [frontend/dist](frontend/dist)，统一通过 http://127.0.0.1:8000 访问前后端，避免跨端口。

如果本机同时有多个模板项目（都使用 `app` 包名）并且经常占用 8000，推荐直接运行：

```powershell
cd backend
.\run-dev-single-port.ps1
```

该脚本会自动：
- 释放 8000 端口监听
- 固定 `PYTHONPATH` 到当前 backend，避免导入到其他项目的 `app`
- 使用 `uv run fastapi dev app/main.py` 在 8000 启动

### 生成新的数据库迁移

```bash
# 在 backend/ 目录下
alembic revision --autogenerate -m "描述你的变更"
alembic upgrade head
```

或通过容器：

```bash
bash scripts/migrate.sh revision --autogenerate -m "描述你的变更"
bash scripts/migrate.sh upgrade head
```

---

## 常见问题

### 启动后后端报 "Can't connect to MySQL"

MySQL 需要约 30 秒完成初始化。`backend_pre_start.py` 会自动重试 60 次，通常会等待成功。如果持续失败，检查 `.env` 中的 MySQL 密码是否与 `compose.yml` 中一致。

### 修改了模型，如何更新数据库？

```bash
cd backend
alembic revision --autogenerate -m "your change description"
alembic upgrade head
```

### 如何重置数据库？

```bash
docker compose down -v   # 删除 volume（⚠️ 会清空所有数据）
docker compose up -d
```
