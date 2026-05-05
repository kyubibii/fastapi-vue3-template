# 快速开始

本文档帮助你在 5 分钟内将项目跑起来。

## 前置条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- [Git](https://git-scm.com/) 已安装

## 步骤一：获取代码

```bash
git clone https://github.com/your-org/fastapi-vue3-template.git
cd fastapi-vue3-template
```

## 步骤二：生成环境配置文件

```bash
bash scripts/generate-env.sh
```

脚本会从 `.env.example` 复制一份 `.env`，并自动生成随机 `SECRET_KEY`。

> **Windows 用户**：可直接复制 `.env.example` 为 `.env`，手动替换 `SECRET_KEY`：
> ```powershell
> Copy-Item .env.example .env
> # 然后编辑 .env，将 SECRET_KEY 替换为一个随机字符串
> ```

## 步骤三：（可选）修改 .env

打开 `.env`，根据需要修改以下字段：

```env
# MySQL 数据库密码（建议修改）
MYSQL_PASSWORD=your_strong_password

# 初始超级管理员
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=changeme123   # ⚠️ 生产环境必须修改！

# SMTP（如需邮件功能）
SMTP_HOST=mailhog
SMTP_PORT=1025
```

## 步骤四：启动所有服务

```bash
docker compose up -d
```

首次启动会：
1. 构建后端镜像（约 1-2 分钟）
2. 构建前端镜像（约 2-3 分钟）
3. 启动 MySQL 8、MailHog、Backend、Frontend

等待所有服务健康：

```bash
docker compose ps
```

所有服务应显示 `healthy` 或 `running`。

## 步骤五：访问应用

| 服务 | 地址 |
|------|------|
| 前端管理界面 | http://localhost |
| 后端 API 文档 | http://localhost:8000/api/v1/docs |
| MailHog 邮件 UI | http://localhost:8025 |

使用默认凭证登录：
- **用户名**：`admin`
- **密码**：`changeme123`

---

## 本地开发

### 后端（无 Docker）

```bash
cd backend

# 创建并激活虚拟环境
uv venv
.\\.venv\\Scripts\\Activate.ps1   # Windows PowerShell

# 安装依赖
uv pip install -e .

# 使用现有 MySQL，按实际情况编辑项目根目录 .env
# 关键项：MYSQL_SERVER / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB

# 启动开发服务器（会自动执行 Alembic upgrade head + initial seed）
uvicorn app.main:app --reload --port 8000
```

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
