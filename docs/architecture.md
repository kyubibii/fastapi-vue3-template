# 架构与 API 设计文档

本文档详细说明项目的系统架构、数据模型和 API 设计原则。

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    浏览器 / 客户端                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS
                   ↓
┌─────────────────────────────────────────────────────────────┐
│            Nginx 反向代理 + 负载均衡 (Frontend)              │
│  ├─ SPA 路由 (/ → index.html)                              │
│  ├─ 静态资源缓存                                            │
│  ├─ gzip 压缩                                              │
│  └─ API 转发 (/api → Backend)                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP
                   ↓
┌─────────────────────────────────────────────────────────────┐
│       FastAPI 应用 (Backend, 可多实例)                       │
├─────────────────────────────────────────────────────────────┤
│ 中间件层:                                                    │
│ ├─ CORS 中间件                                              │
│ ├─ 审计日志中间件 (自动拦截所有非 GET)                      │
│ ├─ 错误处理                                                │
│ └─ 请求日志                                                │
├─────────────────────────────────────────────────────────────┤
│ 路由层:                                                      │
│ ├─ /api/v1/auth (认证)                                     │
│ ├─ /api/v1/users (用户管理)                                │
│ ├─ /api/v1/permissions (权限树)                            │
│ ├─ /api/v1/roles (角色)                                    │
│ ├─ /api/v1/items (业务数据)                                │
│ ├─ /api/v1/audit-logs (审计日志)                          │
│ ├─ /api/v1/jobs (定时任务)                                │
│ └─ /api/v1/settings (系统设置)                             │
├─────────────────────────────────────────────────────────────┤
│ 服务层:                                                      │
│ ├─ 认证服务 (JWT Token 管理)                                │
│ ├─ 权限服务 (RBAC 权限检查)                                │
│ ├─ 业务服务 (核心逻辑)                                      │
│ └─ 第三方集成 (邮件、消息队列等)                            │
├─────────────────────────────────────────────────────────────┤
│ 定时任务层:                                                  │
│ └─ APScheduler (后台定时执行)                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ TCP 3306
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                MySQL 8.0 (数据库)                            │
│  ├─ 主从复制 (可选)                                         │
│  ├─ 备份策略 (日备 + 周备)                                  │
│  ├─ 性能监控 (慢查询日志)                                  │
│  └─ 数据加密 (TLS)                                         │
└─────────────────────────────────────────────────────────────┘
```

### 服务间通信协议

| 服务对 | 协议 | 用途 | 安全性 |
|--------|------|------|--------|
| 浏览器 ↔ Nginx | HTTPS | Web 访问 | TLS 1.3 |
| Nginx ↔ FastAPI | HTTP | 内网转发 | VPC 隔离 |
| FastAPI ↔ MySQL | TCP | 数据库访问 | VPC 隔离 |
| FastAPI → SMTP | SMTP/TLS | 邮件发送 | TLS |
| FastAPI → Sentry | HTTPS | 错误上报 | TLS |

---

## 📊 数据模型

### 核心实体关系图

```
用户管理：
┌──────────┐      ┌──────────┐
│  User   │◄────-┤  Role   │
│(用户)   │  N:M  │(角色)   │
└──────────┘      └──────────┘
     │                  │
     │                  │
     │            ┌──────────┐
     │            │Permission│
     │            │ (权限)   │
     └───────────►└──────────┘

权限树：
┌─────────────────┐
│PermissionGroup  │(权限组，如：用户管理)
│                 │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│PermissionPage   │(权限页，如：用户列表)
│                 │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Permission      │(权限点，如：查看)
│ full_code:      │
│ user.users.read │
└─────────────────┘

业务数据：
┌────────┐       ┌────────┐
│  Item  │◄────-►│Comment │
│(物品)  │  1:N  │(评论)  │
└────────┘       └────────┘
     ▲
     │ author
┌────────┐
│  User  │
└────────┘

审计追踪：
┌─────────────┐
│ AuditLog    │
├─────────────┤
│ user_id     │──┐
│ module      │  │
│ action      │  └──► 关联 User
│ status_code │
│ timestamp   │
└─────────────┘
```

### 数据库表设计

#### 1. User (用户表)

```sql
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,     -- Argon2 或 Bcrypt 哈希
    is_superuser BOOLEAN DEFAULT FALSE,         -- 超管标记
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,                        -- 软删除时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_deleted_at (deleted_at)
);
```

#### 2. Role (角色表)

```sql
CREATE TABLE role (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_builtin BOOLEAN DEFAULT FALSE,           -- 内置角色（不可删除）
    deleted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_deleted_at (deleted_at)
);

-- 用户-角色关联
CREATE TABLE user_role (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    
    INDEX idx_role_id (role_id)
);
```

#### 3. Permission 权限树

```sql
CREATE TABLE permission_group (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,           -- 权限组码：user_mgmt
    description TEXT,
    sort_order INT DEFAULT 0,
    
    INDEX idx_code (code)
);

CREATE TABLE permission_page (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,                  -- 权限页码：users
    page_url VARCHAR(200),                      -- 前端路由：/users
    description TEXT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (group_id) REFERENCES permission_group(id),
    UNIQUE KEY (group_id, code),
    INDEX idx_group_id (group_id)
);

CREATE TABLE permission (
    id INT PRIMARY KEY AUTO_INCREMENT,
    page_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,                  -- 操作码：read / create / update / delete
    full_code VARCHAR(150) UNIQUE NOT NULL,    -- 完整码：user_mgmt.users.read
    is_builtin BOOLEAN DEFAULT FALSE,
    description TEXT,
    
    FOREIGN KEY (page_id) REFERENCES permission_page(id),
    INDEX idx_full_code (full_code),
    INDEX idx_page_id (page_id)
);

-- 角色-权限关联
CREATE TABLE role_permission (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE,
    
    INDEX idx_permission_id (permission_id)
);
```

#### 4. AuditLog (审计日志表)

```sql
CREATE TABLE audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    module VARCHAR(50),                         -- 模块：users / items / roles
    action VARCHAR(50),                         -- 操作：create / update / delete
    path VARCHAR(500),                          -- 请求路径
    method VARCHAR(10),                         -- HTTP 方法
    status_code INT,                            -- 响应状态码
    request_body LONGTEXT,                      -- 请求体（脱敏）
    response_body LONGTEXT,                     -- 响应体（脱敏）
    ip_address VARCHAR(45),                     -- 客户端 IP
    user_agent TEXT,                            -- User-Agent
    duration_ms INT,                            -- 请求耗时（毫秒）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_module (module),
    INDEX idx_action (action)
);
```

#### 5. Item (业务数据示例)

```sql
CREATE TABLE item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INT NOT NULL,
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    deleted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (owner_id) REFERENCES user(id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_status (status),
    INDEX idx_deleted_at (deleted_at),
    FULLTEXT INDEX ft_name_description (name, description)  -- 全文搜索
);
```

---

## 🔌 API 接口设计

### 命名约定

```
版本控制：/api/v1/          ← 在 URL 中体现版本
资源复数：/users /roles     ← 统一使用复数形式
嵌套资源：/users/{id}/roles ← 表示用户的所有角色
查询参数：?skip=0&limit=10  ← 分页参数

例外：
/api/v1/auth/login          ← 认证操作使用动词
/api/v1/auth/logout         ← 但尽量少用
```

### 认证相关

#### 登录

**请求：**
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=admin&password=changeme123
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "AbCdEfGhIjKlMnOpQrStUvWxYz...",
  "token_type": "bearer",
  "expires_in": 900  // 秒数
}
```

**机制：**
- Access Token: JWT，15分钟有效期，用于 API 请求
- Refresh Token: Opaque Token，30天有效期，存储于 httpOnly Cookie

#### 刷新令牌

**请求：**
```http
POST /api/v1/auth/refresh HTTP/1.1
Cookie: refresh_token=AbCdEfGhIjKlMnOpQrStUvWxYz...
```

**响应：**
```json
{
  "access_token": "新的 JWT...",
  "refresh_token": "新的 Opaque Token...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**特性：**
- 每次刷新生成新的 Refresh Token
- 旧 Refresh Token 失效（防重放）
- Hash 存储在数据库，原始 Token 仅返回一次

#### 登出

**请求：**
```http
POST /api/v1/auth/logout HTTP/1.1
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "message": "Logged out successfully"
}
```

### 用户管理

#### 获取当前用户信息

**请求：**
```http
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator",
  "is_superuser": true,
  "is_active": true,
  "roles": [
    {
      "id": 1,
      "name": "Superuser"
    }
  ],
  "permissions": [
    "*"  // 超管拥有所有权限
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 获取用户列表

**请求：**
```http
GET /api/v1/users?skip=0&limit=10&search=admin HTTP/1.1
Authorization: Bearer <access_token>
```

**查询参数：**
| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| skip | int | 分页偏移 | 0 |
| limit | int | 每页条数 | 10 |
| search | str | 用户名/邮箱搜索 | 无 |
| is_active | bool | 活跃状态过滤 | 无 |

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "Administrator",
      "is_superuser": true,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

#### 创建用户

**请求：**
```json
POST /api/v1/users HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "SecurePassword123!",
  "is_active": true,
  "role_ids": [2, 3]  // 分配角色
}
```

**验证规则：**
- username: 4-100 字符，仅字母数字下划线
- email: 有效的邮箱格式
- password: 8-100 字符，需要大小写字母、数字、特殊符号
- role_ids: 必须引用存在的角色

**响应：**
```json
{
  "id": 2,
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_active": true,
  "roles": [
    { "id": 2, "name": "Editor" },
    { "id": 3, "name": "Viewer" }
  ],
  "created_at": "2024-05-06T14:30:00Z"
}
```

### 权限树 API

#### 获取权限树（含权限组、页面、权限点）

**请求：**
```http
GET /api/v1/permissions/tree HTTP/1.1
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "groups": [
    {
      "id": 1,
      "name": "用户管理",
      "code": "user_mgmt",
      "pages": [
        {
          "id": 1,
          "name": "用户列表",
          "code": "users",
          "page_url": "/users",
          "permissions": [
            {
              "id": 1,
              "name": "查看",
              "code": "read",
              "full_code": "user_mgmt.users.read"
            },
            {
              "id": 2,
              "name": "新增",
              "code": "create",
              "full_code": "user_mgmt.users.create"
            }
          ]
        }
      ]
    }
  ]
}
```

### 角色管理

#### 获取角色详情（含权限）

**请求：**
```http
GET /api/v1/roles/{role_id} HTTP/1.1
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": 1,
  "name": "Editor",
  "description": "可编辑内容的角色",
  "permissions": [
    "content.items.read",
    "content.items.create",
    "content.items.update"
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 更新角色权限

**请求：**
```json
PUT /api/v1/roles/{role_id}/permissions HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "permission_ids": [1, 2, 3]  // 新权限列表
}
```

**响应：**
```json
{
  "id": 1,
  "name": "Editor",
  "permissions": [1, 2, 3]
}
```

### 审计日志 API

#### 查询审计日志

**请求：**
```http
GET /api/v1/audit-logs?skip=0&limit=50&user_id=2&start_date=2024-05-01&end_date=2024-05-06 HTTP/1.1
Authorization: Bearer <access_token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| skip | int | 分页偏移 |
| limit | int | 每页条数 |
| user_id | int | 用户 ID 过滤 |
| module | str | 模块过滤（users / items / roles） |
| action | str | 操作过滤（create / update / delete） |
| status_code | int | 状态码过滤 |
| start_date | date | 开始日期（ISO 8601） |
| end_date | date | 结束日期（ISO 8601） |

**响应：**
```json
{
  "items": [
    {
      "id": 123,
      "user_id": 1,
      "username": "admin",
      "module": "users",
      "action": "create",
      "path": "/api/v1/users",
      "method": "POST",
      "status_code": 201,
      "request_body": {"username": "john", ...},
      "response_body": {"id": 2, "username": "john", ...},
      "ip_address": "192.168.1.100",
      "duration_ms": 45,
      "created_at": "2024-05-06T14:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

---

## 🔒 安全设计

### 密码哈希与验证

```python
# 支持两种算法透明升级
password_hash = PasswordHash((
    Argon2Hasher(),  # 优先（新）
    BcryptHasher()   # 兼容（旧）
))

# 验证过程
is_valid, upgraded_hash = password_hash.verify_and_update(plain, hashed)
if upgraded_hash:
    # 用户密码自动升级，保存新哈希
    db_user.hashed_password = upgraded_hash
    session.add(db_user)
    session.commit()
```

### JWT Token 结构

**Access Token 载荷：**
```json
{
  "sub": "admin",           // 用户名
  "exp": 1714998600,        // 过期时间戳
  "type": "access",         // Token 类型
  "iat": 1714994400         // 签发时间戳
}
```

**Refresh Token：**
- 完全随机的 Opaque Token（无可解码信息）
- SHA-256 哈希后存储在数据库
- httpOnly、Secure、SameSite=Strict Cookie

### SQL 注入防护

所有数据库查询使用参数化查询（SQLModel 自动处理）：

```python
# ✓ 安全（参数化）
stmt = select(User).where(User.username == username)
user = session.exec(stmt).first()

# ✗ 不安全（字符串拼接）
query = f"SELECT * FROM user WHERE username = '{username}'"
```

### 敏感数据脱敏

审计日志自动脱敏敏感字段：

```python
SENSITIVE_FIELDS = {
    'password', 'hashed_password',
    'token', 'refresh_token',
    'secret_key', 'api_key',
    'credit_card', 'ssn'
}

# 脱敏示例
{
  "username": "admin",
  "password": "***REDACTED***",  # 自动脱敏
  "email": "admin@example.com"
}
```

---

## 📈 性能设计

### 缓存策略

```python
# 数据库查询缓存（应用层）
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_permission_tree():
    # 权限树变化不频繁，缓存 1 小时
    return fetch_from_db()

# 前端资源缓存（HTTP）
# Nginx 配置：
# expires 30d  # 静态资源缓存 30 天
# Cache-Control: public, immutable
```

### 分页设计

```python
# 标准分页响应
{
  "items": [...],
  "total": 100,      // 总数
  "skip": 0,
  "limit": 10        // 每页数
}

# 游标分页（大数据集）
{
  "items": [...],
  "next_cursor": "AbCdEfGhIjKlMnOpQrStUvWxYz",
  "has_more": true
}
```

### N+1 查询优化

```python
# ✗ N+1 问题
users = session.query(User).all()
for user in users:
    print(user.roles)  # 每个用户查询一次 role

# ✓ 使用 selectinload
from sqlalchemy.orm import selectinload
users = session.query(User).options(
    selectinload(User.roles)
).all()

# ✓ 或 joinedload
from sqlalchemy.orm import joinedload
users = session.query(User).options(
    joinedload(User.roles)
).all()
```

---

## 🔄 错误处理

### HTTP 状态码规范

| 码 | 含义 | 用途 |
|----|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功（无响应体） |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证（缺少 Token） |
| 403 | Forbidden | 无权限（权限不足） |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 冲突（如邮箱已存在） |
| 422 | Unprocessable Entity | 验证错误 |
| 500 | Internal Server Error | 服务器错误 |

### 错误响应格式

```json
{
  "detail": "用户名已存在",
  "error_code": "DUPLICATE_USERNAME",
  "status_code": 409,
  "timestamp": "2024-05-06T14:30:00Z"
}
```

---

## 📚 参考资源

- [RESTful API 设计指南](https://restfulapi.net/)
- [FastAPI 安全](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT 最佳实践](https://tools.ietf.org/html/rfc8949)
- [OWASP 安全检查清单](https://cheatsheetseries.owasp.org/)