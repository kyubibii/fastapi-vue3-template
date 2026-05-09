# 📚 完整文档索引

欢迎！本页面提供项目所有文档的统一入口，帮助你快速找到所需信息。

---

## 🎯 按用户角色分类

### 👨‍💼 产品经理 / 项目经理

**了解项目概况与功能：**

1. **[README.md](../README.md)** - 项目总览
   - 核心能力概览
   - 技术栈详解
   - 功能特性说明
   - 基础设施架构

2. **[快速开始 - 容器化部分](quick-start.md#方案-a容器化部署docker-compose)** - 5 分钟体验
   - 完整应用栈演示
   - 默认账号密码

---

### 👨‍💻 前端开发者

**开始开发前，必读：**

1. **[快速开始 - 本地开发](quick-start.md#方案-b本地开发无-docker)** - 启动开发环境
   - 前端开发服务器配置
   - 依赖安装
   - 热重载开发流程

2. **[开发指南 - 前端部分](development.md#-前端开发)** - 工作流详解
   - 代码检查与格式化
   - 测试运行
   - 常见问题解答

3. **[架构设计 - API 设计](architecture.md#-api-接口设计)** - API 调用指南
   - 认证流程（登录、令牌刷新）
   - 权限检查集成
   - 用户/角色/权限 API 调用示例

4. **[快速开始 - 故障排查](quick-start.md#-故障排查)** - 遇到问题
   - 常见错误解决方案
   - 日志查看方法

**核心代码位置：**
- 路由：`frontend/src/router/` - Vue Router 路由定义 + 权限守卫
- API 调用：`frontend/src/api/` - Axios 封装
- 状态管理：`frontend/src/stores/` - Pinia store（auth、permission）
- 页面：`frontend/src/views/` - 业务页面组件
- 布局：`frontend/src/layouts/` - AdminLayout（侧边栏、顶部栏）

---

### 🔧 后端开发者

**开始开发前，必读：**

1. **[快速开始 - 本地开发](quick-start.md#方案-b本地开发无-docker)** - 启动开发环境
   - Python 虚拟环境配置
   - 依赖安装
   - 自动迁移与初始化

2. **[开发指南 - 完整内容](development.md)** - 核心开发文档
   - 项目分层架构说明
   - **添加新功能的完整流程**（模型 → Schema → CRUD → 路由）
   - 权限检查与 RBAC 集成
   - 数据库迁移管理
   - 测试编写
   - 代码规范

3. **[架构设计 - 数据模型](architecture.md#-数据模型)** - 数据库设计
   - 核心实体关系图
   - 完整表结构（User、Role、Permission、AuditLog 等）
   - 索引策略

4. **[架构设计 - API 设计](architecture.md#-api-接口设计)** - API 设计规范
   - 命名约定
   - 认证/授权 API（登录、刷新、当前用户）
   - 用户/角色/权限 管理 API
   - 审计日志查询 API
   - 状态码与错误处理

5. **[快速开始 - 故障排查](quick-start.md#-故障排查)** - 本地开发问题解决
   - MySQL 连接失败
   - Alembic 迁移错误
   - 虚拟环境问题

6. **[微信支付 JSAPI / 小程序接入](wechat-pay-jsapi.md)** - 支付对接必读
   - 商户侧与后台配置项（必填项清单）
   - 小程序 `openid`、`wx.requestPayment`、回调 URL 说明
   - 与模板内置 `wechat_pay` 路由、SDK 的对应关系

**核心代码位置：**
- 入口：`backend/app/main.py` - FastAPI 应用入口
- 配置：`backend/app/core/` - 数据库、安全、运行时配置
- 模型：`backend/app/models/` - SQLModel 数据模型（对应数据库表）
- Schema：`backend/app/schemas/` - Pydantic 请求/响应验证
- CRUD：`backend/app/crud/` - 数据库操作（Create、Read、Update、Delete）
- 路由：`backend/app/api/routes/` - FastAPI 路由与业务逻辑（含 `wechat_pay.py` 微信支付示例）
- 依赖注入：`backend/app/api/deps.py` - 认证、权限、数据库会话注入
- 中间件：`backend/app/middleware/` - 审计日志拦截
- 迁移：`backend/app/alembic/` - Alembic 版本管理

---

### 🚀 运维 / DevOps 工程师

**部署与运维指南：**

1. **[快速开始 - 容器化部署](quick-start.md#方案-a容器化部署docker-compose)** - 生产初级部署
   - Docker Compose 配置
   - 环境变量设置
   - 第一次启动检查清单

2. **[部署指南 - 完整内容](deployment.md)** - 生产级部署文档
   - **部署前安全审计清单**
   - **Docker Compose 生产配置**（含 Nginx HTTPS、MySQL 优化、容器编排）
   - **云平台部署**（AWS ECS、Azure Container Instances）
   - **SSL 证书申请与配置**（Let's Encrypt + Certbot）
   - **监控与告警**（Sentry、慢查询日志）
   - **备份与恢复策略**
   - **更新与回滚流程**
   - **性能调优**（数据库索引、连接池）
   - **故障处理常见问题**

3. **[架构设计 - 系统架构](architecture.md#-系统架构)** - 技术架构理解
   - 整体架构图
   - 服务间通信协议
   - 性能设计细节

**关键配置文件：**
- `.env` - 环境变量（数据库、SMTP、认证密钥等）
- `compose.yml` - Docker Compose 编排配置
- `backend/Dockerfile` - 后端容器构建
- `frontend/Dockerfile` - 前端容器构建
- `backend/alembic.ini` - 数据库迁移配置
- `backend/my.cnf` - MySQL 性能调优配置（见部署指南）

---

## 📖 按任务分类

### 我想启动项目

**选择你的场景：**

- **需要完整体验（包括数据库）** → [快速开始 - 容器化部署](quick-start.md#方案-a容器化部署docker-compose)
- **只想开发后端（用现有 MySQL）** → [快速开始 - 本地开发 - 后端部分](quick-start.md#步骤-3启动后端)
- **只想开发前端（无后端）** → [快速开始 - 本地开发 - 前端部分](quick-start.md#步骤-4启动前端)

---

### 我想添加新功能

**完整流程：**

1. 阅读 [开发指南 - 添加新功能流程](development.md#-添加新功能的完整流程) 
   - 按步骤操作：定义模型 → 定义 Schema → 实现 CRUD → 定义路由 → 生成迁移 → 前端实现

2. 参考现有代码（如 Item 功能）理解目录结构

3. 遵循 [开发指南 - 代码规范](development.md#-代码规范) 提交代码

---

### 我想部署到生产

**完整流程：**

1. 阅读 [部署指南 - 部署前检查清单](deployment.md#-部署前检查清单)
   - 安全审计
   - 性能审计

2. 选择部署方案：
   - **简单部署**（单机）→ [部署指南 - Docker Compose 部署](deployment.md#-docker-compose-部署推荐用于小规模)
   - **云平台部署** → [部署指南 - 云平台部署](deployment.md#-云平台部署awsazuregcp)

3. 准备环境变量，参考 `.env.example`

4. 执行部署，参考相应章节步骤

---

### 我遇到了问题

**找到解决方案：**

1. **项目启动失败**
   - 容器化：[快速开始 - 故障排查 - 容器化部署](quick-start.md#容器化部署)
   - 本地开发：[快速开始 - 故障排查 - 本地开发](quick-start.md#本地开发)

2. **数据库问题**
   - 迁移失败：[开发指南 - 数据库迁移](development.md#-数据库迁移管理)
   - 部署后问题：[部署指南 - 故障处理](deployment.md#-故障处理)

3. **认证/权限问题**
   - 理解权限系统：[开发指南 - 权限系统](development.md#-权限系统使用)
   - API 设计：[架构设计 - 认证与权限 API](architecture.md#认证相关)

4. **API 调用问题**
   - API 文档：[架构设计 - API 接口设计](architecture.md#-api-接口设计)
   - 在线文档：http://localhost:8000/api/v1/docs（项目运行后）

5. **性能问题**
   - 后端优化：[开发指南 - 性能优化](development.md#-性能优化)
   - 部署优化：[部署指南 - 性能基准与调优](deployment.md#-性能基准与调优)

---

## 🗂️ 文件树状视图

```
docs/
├── index.md                    ← 你在这里 📍
├── quick-start.md              # 快速开始（初次启动必读）
├── development.md              # 开发指南（添加功能必读）
├── architecture.md             # 架构设计（理解系统必读）
├── deployment.md               # 部署指南（生产部署必读）
└── wechat-pay-jsapi.md         # 微信支付 JSAPI / 小程序接入

项目根目录/
├── README.md                   # 项目总览（功能与技术栈）
├── .env.example                # 环境变量模板
├── compose.yml                 # Docker Compose 编排
├── backend/
│   ├── pyproject.toml          # Python 依赖
│   ├── Dockerfile              # 后端容器镜像
│   ├── app/
│   │   ├── main.py             # 应用入口
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # 请求/响应验证
│   │   ├── crud/               # 数据库操作
│   │   ├── api/                # API 路由
│   │   └── core/               # 配置与工具
│   └── alembic/                # 数据库迁移
└── frontend/
    ├── package.json            # npm 依赖
    ├── Dockerfile              # 前端容器镜像
    └── src/
        ├── api/                # Axios 封装
        ├── stores/             # Pinia 状态管理
        ├── router/             # Vue Router 路由
        └── views/              # 页面组件
```

---

## 🔍 快速导航表

| 我要... | 去... | 文档 | 行数 |
|--------|------|------|------|
| 启动项目 | 5分钟看完 | quick-start.md | 50 |
| 添加新功能 | 按步骤操作 | development.md | ~500 |
| 理解系统 | 读架构与模型 | architecture.md | ~400 |
| 部署上线 | 完整清单 | deployment.md | ~600 |
| 查看 API | 实时文档 | http://localhost:8000/api/v1/docs | ✨ |
| 看代码示例 | 以 Item 功能为例 | development.md#1️⃣-定义数据模型 | ~200 |
| 理解权限 | RBAC 详解 | development.md#-权限系统使用 | ~100 |
| 优化性能 | 索引与缓存 | deployment.md 或 development.md | ~100 |

---

## 📞 获取帮助

### 文档中找不到答案？

1. **检查相关文档中的"常见问题"章节**
   - 快速开始：[Q1-Q4](quick-start.md#-常见问题)
   - 开发指南：[Q1-Q4](development.md#-常见开发问题)

2. **查看在线 API 文档**
   - 启动项目后访问：http://localhost:8000/api/v1/docs
   - 可在线测试 API

3. **搜索代码注释**
   - 项目代码中有详细的中文注释
   - 从 `backend/app/main.py` 或 `frontend/src/main.ts` 开始

4. **提交 GitHub Issue**
   - 提供：错误日志、环境信息、重现步骤
   - 标题格式：`[bug] 问题描述` 或 `[feature] 功能建议`

---

## 📊 学习路径建议

### 🟢 初级（1-2 天）

1. 阅读 README.md 了解整体
2. 按 [快速开始](quick-start.md) 启动项目
3. 登录管理界面，浏览功能
4. 访问 http://localhost:8000/api/v1/docs 查看 API

**输出**：能启动项目，理解基础功能

### 🟡 中级（3-5 天）

1. 根据 [开发指南](development.md) 添加一个新功能
2. 学习 [权限系统](development.md#-权限系统使用) 的使用
3. 修改现有功能（如 Item 的字段）并生成迁移

**输出**：能独立开发新功能，理解权限系统

### 🔴 高级（1-2 周）

1. 学习 [架构设计](architecture.md) 的完整内容
2. 根据 [部署指南](deployment.md) 部署到测试环境
3. 配置监控、日志、备份等生产配置
4. 性能优化与安全加固

**输出**：能独立维护生产环境，设计大型功能

---

**最后更新**：2026 年 5 月 6 日

💡 **提示**：将本页面加入浏览器书签，方便后续查阅！