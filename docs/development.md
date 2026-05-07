# 开发指南

本文档详细说明项目的开发工作流、代码组织、最佳实践等。

---

## 🏗️ 项目架构概览

### 分层架构

```
前端层 (Vue3 + TypeScript)
       ↓ API 调用 (Axios)
API 网关 (Nginx 反向代理 + 路由守卫)
       ↓ 转发请求
路由层 (FastAPI @router)
       ↓
服务层 (依赖注入 Depends)
   ├─ 认证 (JWT 解析)
   ├─ 权限检查 (RBAC 匹配)
   └─ 业务逻辑
       ↓
数据访问层 (CRUD 操作)
       ↓
数据库层 (MySQL + Alembic)
```

### 代码分层职责

| 层级 | 目录 | 职责 | 示例 |
|------|------|------|------|
| **API 层** | `api/routes/` | 路由、参数验证、响应格式化 | `users.py` 定义 `GET /api/v1/users` |
| **服务层** | `api/deps.py` | 业务逻辑、权限检查、事务管理 | 检查用户权限、计算统计数据 |
| **CRUD 层** | `crud/` | 数据库查询操作 | 查询、插入、更新、删除用户 |
| **模型层** | `models/` | 数据模型（表结构） | `User` 对应 `users` 表 |
| **Schema 层** | `schemas/` | 请求/响应验证 | 登录请求格式、用户响应格式 |

---

## 🔖 内置枚举与数据字典

### 选型规则

- 固定业务语义（例如 `gender`、状态机）使用后端内置枚举：`backend/app/constants/enums.py`。
- 可运营配置项（可在后台频繁增删改）使用数据字典表（`dictionary_type` / `dictionary_item`）。

### 自动同步机制（后端 -> 前端）

- 后端枚举变更后，执行前端同步命令：`pnpm run enums:sync`。
- 同步命令会调用后端导出脚本：`backend/scripts/export_enums.py`。
- 生成文件：`frontend/src/constants/generated/enums.gen.ts`（自动生成，不手改）。
- 前端业务常量从 `frontend/src/constants/` 统一导出并消费。

### 开发流程

1. 修改 `backend/app/constants/enums.py`。
2. 运行 `pnpm run enums:sync`。
3. 运行 `pnpm build` 或 `pnpm dev` 验证。
4. 提交后端枚举变更和生成后的前端枚举文件。

---

## 📝 添加新功能的完整流程

本例演示如何添加一个"评论"功能。

### 1️⃣ 定义数据模型

`backend/app/models/comment.py`：

```python
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class Comment(SQLModel, table=True):
    """评论模型"""
    
    __tablename__ = "comment"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    content: str = Field(max_length=2000)
    deleted_at: datetime | None = Field(default=None)  # 软删除
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

在 `backend/app/models/__init__.py` 导出：

```python
from .comment import Comment

__all__ = ["Comment", ...]
```

### 2️⃣ 定义 Schema（请求/响应）

`backend/app/schemas/comment.py`：

```python
from datetime import datetime
from pydantic import BaseModel, Field

class CommentCreate(BaseModel):
    """创建评论请求"""
    item_id: int = Field(..., description="物品 ID")
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")

class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: str = Field(..., min_length=1, max_length=2000)

class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    user_id: int
    item_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # SQLModel 兼容
```

### 3️⃣ 实现 CRUD 操作

`backend/app/crud/comment.py`：

```python
from sqlmodel import Session, select
from app.models.comment import Comment
from app.crud.base import CRUDBase
from app.schemas.comment import CommentCreate, CommentUpdate

class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    """评论 CRUD 操作"""
    pass

comment = CRUDComment(Comment)
```

在 `backend/app/crud/__init__.py` 导出：

```python
from .comment import comment

__all__ = ["comment", ...]
```

### 4️⃣ 定义路由

`backend/app/api/routes/comments.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.crud.comment import comment
from app.models.user import User
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    comment_in: CommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CommentResponse:
    """创建评论（需要登录）"""
    # 检查物品是否存在
    item = session.get(Item, comment_in.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    
    # 创建评论
    db_comment = Comment(
        **comment_in.dict(),
        user_id=current_user.id,
    )
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    session: Session = Depends(get_session),
) -> CommentResponse:
    """获取评论详情"""
    db_comment = session.get(Comment, comment_id)
    if not db_comment or db_comment.deleted_at:
        raise HTTPException(status_code=404, detail="评论不存在")
    return db_comment

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CommentResponse:
    """更新评论（仅作者可修改）"""
    db_comment = session.get(Comment, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 权限检查
    if db_comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权限修改")
    
    # 更新
    db_comment.content = comment_in.content
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """软删除评论（标记 deleted_at）"""
    db_comment = session.get(Comment, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 权限检查
    if db_comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权限删除")
    
    # 软删除
    from datetime import datetime, timezone
    db_comment.deleted_at = datetime.now(timezone.utc)
    session.add(db_comment)
    session.commit()
```

在 `backend/app/api/main.py` 注册路由：

```python
from app.api.routes.comments import router as comments_router

api_router.include_router(comments_router)
```

### 5️⃣ 将新功能接入权限树（关键步骤）

新功能不仅要有 API 和页面，还需要进入 RBAC 权限树，否则前端菜单和权限控制无法完整生效。

当前项目的权限树是三层结构：

```text
PermissionGroup -> PermissionPage -> Permission
```

例如评论功能可设计为：

```text
content.comments.read
content.comments.create
content.comments.update
content.comments.delete
content.comments.export
```

#### 方式 A：通过权限管理 API 动态新增（推荐日常开发）

1. 新增权限页面（会自动生成 read/create/update/delete 四个内置动作）

```bash
# 先获取 content 组的 group_id（可通过 GET /api/v1/permissions/tree 查看）
curl -X POST "http://localhost:8000/api/v1/permissions/pages" \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{
        "group_id": 1,
        "name": "评论管理",
        "code": "comments",
        "page_url": "/comments",
        "sort_order": 20
    }'
```

2. 按需新增自定义动作（如 export / approve）

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/pages/{page_id}/actions?action_code=export&action_name=导出评论" \
    -H "Authorization: Bearer <access_token>"
```

3. 将新权限分配给角色

```bash
# 先通过 GET /api/v1/permissions/tree 拿到 permission_ids
curl -X PUT "http://localhost:8000/api/v1/roles/{role_id}/permissions" \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"permission_ids": [101, 102, 103, 104, 105]}'
```

4. 前端登录后重新拉取权限，验证菜单和按钮权限是否生效。

#### 方式 B：在初始化种子中固化（推荐内置模块）

如果评论是模板内置能力，建议把它写入 `backend/app/initial_data.py` 的 `_PERM_TREE`，这样新环境启动时自动具备该权限树。

示例（在 `内容管理` 下新增 `评论管理` 页面）：

```python
_PERM_TREE = [
        (
                "内容管理", "content", 10,
                [
                        ("物品管理", "items", "/items", 10, ["export"]),
                        ("评论管理", "comments", "/comments", 20, ["export"]),
                ],
        ),
        # ...
]
```

更新后执行初始化（或重启触发自动 seed）：

```bash
cd backend
python -m app.initial_data
```

#### 在路由中落地权限校验

为评论接口加上权限依赖（示例）：

```python
from app.api.deps import require_permission

@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
        comment_in: CommentCreate,
        _: User = Depends(require_permission("content.comments.create")),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
) -> CommentResponse:
        ...
```

建议映射关系：

- 列表/详情查询 -> `content.comments.read`
- 新增评论 -> `content.comments.create`
- 编辑评论 -> `content.comments.update`
- 删除评论 -> `content.comments.delete`
- 导出评论 -> `content.comments.export`

### 6️⃣ 生成数据库迁移

```bash
cd backend

# Alembic 对比模型与上次迁移，生成差异
alembic revision --autogenerate -m "add comment table"

# 查看生成的迁移文件
cat app/alembic/versions/<timestamp>_add_comment_table.py

# 应用迁移
alembic upgrade head
```

### 7️⃣ 前端实现（可选）

`frontend/src/api/comments.ts`：

```typescript
import request from './index';

export function createComment(itemId: number, content: string) {
  return request.post('/comments', {
    item_id: itemId,
    content,
  });
}

export function getComment(commentId: number) {
  return request.get(`/comments/${commentId}`);
}

export function updateComment(commentId: number, content: string) {
  return request.put(`/comments/${commentId}`, { content });
}

export function deleteComment(commentId: number) {
  return request.delete(`/comments/${commentId}`);
}
```

---

## 🔐 权限系统使用

### 理解权限码格式

权限码三层结构：`{group}.{page}.{action}`

```
user_mgmt.users.read         ← 用户管理 > 用户列表 > 查看
user_mgmt.users.create       ← 用户管理 > 用户列表 > 新增
user_mgmt.roles.delete       ← 用户管理 > 角色 > 删除
content.items.export         ← 内容管理 > 物品 > 导出
```

### 在 API 中检查权限

`backend/app/api/deps.py` 已提供权限检查函数：

```python
def require_permission(permission_code: str):
    """权限检查装饰器"""
    async def check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        if permission_code not in current_user.permissions:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return check
```

使用示例：

```python
from app.api.deps import require_permission

@router.post("/items", response_model=ItemResponse)
async def create_item(
    item_in: ItemCreate,
    _: User = Depends(require_permission("content.items.create")),
    session: Session = Depends(get_session),
) -> ItemResponse:
    """创建物品（需要 content.items.create 权限）"""
    ...
```

### 在前端中检查权限

前端已集成权限检查：

```typescript
// src/stores/permission.ts
import { defineStore } from 'pinia';

export const usePermissionStore = defineStore('permission', () => {
  const permissions = ref<string[]>([]);
  
  const hasPermission = (code: string) => {
    const auth = useAuthStore();
    if (auth.user?.is_superuser) return true;
    return permissions.value.includes(code);
  };
  
  return { permissions, hasPermission };
});

// 使用示例
const permissionStore = usePermissionStore();
if (permissionStore.hasPermission('content.items.create')) {
  // 显示"新增"按钮
}
```

---

## 🗄️ 数据库迁移管理

### 创建迁移

```bash
cd backend

# 自动生成迁移（推荐）
alembic revision --autogenerate -m "add user email column"

# 手动创建空迁移（复杂业务逻辑）
alembic revision -m "populate user emails"
```

### 查看迁移历史

```bash
# 显示已应用的迁移
alembic current

# 显示所有迁移及状态
alembic history --verbose

# 显示两个版本间的 SQL
alembic upgrade <revision_from>:<revision_to> --sql
```

### 应用/回滚迁移

```bash
# 应用到最新版本
alembic upgrade head

# 应用特定版本
alembic upgrade abc123def456

# 回滚上一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade abc123def456
```

### 迁移最佳实践

1. **每个迁移只做一件事**
   ```python
   # ✓ 好
   alembic revision -m "add user.email"
   alembic revision -m "add unique constraint on email"
   
   # ✗ 差
   alembic revision -m "modify user table and add role table"
   ```

2. **编写可回滚的迁移**
   ```python
   def upgrade() -> None:
       op.add_column('user', sa.Column('email', sa.String(255)))
   
   def downgrade() -> None:
       op.drop_column('user', 'email')
   ```

3. **避免生产环境数据损失**
   ```python
   # 修改列类型前备份数据
   def upgrade() -> None:
       # 创建临时列
       op.add_column('user', sa.Column('status_new', sa.Integer()))
       # 迁移数据
       op.execute("UPDATE user SET status_new = CAST(status AS INT)")
       # 删除旧列、重命名新列
       op.drop_column('user', 'status')
       op.rename_table('user', ...)
   ```

---

## 🧪 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_users.py

# 运行特定测试用例
pytest tests/test_users.py::test_create_user

# 生成覆盖率报告
pytest --cov=app

# 显示打印日志
pytest -s tests/test_users.py
```

### 编写测试示例

`backend/tests/test_comments.py`：

```python
import pytest
from httpx import AsyncClient
from sqlmodel import Session

@pytest.fixture
async def client(session: Session):
    """测试客户端"""
    app = FastAPI()
    # 挂载路由...
    return AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient, session: Session):
    """测试创建评论"""
    # 创建测试用户和物品
    user = create_test_user(session)
    item = create_test_item(session)
    
    # 调用 API
    response = await client.post(
        "/comments",
        json={"item_id": item.id, "content": "很好！"},
        headers={"Authorization": f"Bearer {user.access_token}"},
    )
    
    # 断言
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "很好！"
    assert data["user_id"] == user.id
```

### 前端测试

```bash
cd frontend

# 目前未集成测试框架，建议使用 Vitest
pnpm add -D vitest

# 运行测试
pnpm run test
```

---

## 📄 代码规范

### Python 代码风格

项目使用 **Ruff** 自动格式化，配置在 `backend/pyproject.toml`：

```bash
cd backend

# 检查代码
ruff check app

# 自动修复
ruff check app --fix

# 格式化
ruff format app

# 类型检查（strict mode）
mypy app
```

示例配置：
```toml
[tool.ruff]
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]  # 启用的规则
ignore = ["E501", "B008"]                        # 忽略的规则
```

### TypeScript 代码风格

前端使用 **ESLint**，配置在 `.eslintrc`（若有）：

```bash
cd frontend

# 检查代码
pnpm run lint

# 自动修复
pnpm run lint --fix
```

### 提交消息规范

遵循 Conventional Commits：

```
feat: add comment feature          # 新功能
fix: fix user login bug            # 修复
docs: update README                # 文档
refactor: extract comment service  # 代码重构
test: add comment tests            # 测试
chore: update dependencies         # 维护
```

---

## 🐛 常见开发问题

### Q1：如何调试异步代码？

A：使用 `asyncio` 调试：

```python
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

async def main():
    result = await some_async_function()
    print(result)

asyncio.run(main())
```

### Q2：如何使用数据库事务？

A：FastAPI 自动处理事务（除非显式禁用）：

```python
@router.post("/transfer")
async def transfer_money(
    from_user_id: int,
    to_user_id: int,
    amount: float,
    session: Session = Depends(get_session),
):
    # 自动在 Depends 中启动事务
    # 若 endpoint 抛出异常，自动回滚
    # 若正常返回，自动提交
    ...
```

### Q3：如何在 API 中返回文件？

A：使用 `FileResponse`：

```python
from fastapi.responses import FileResponse

@router.get("/download/{file_id}")
async def download_file(file_id: int):
    file_path = f"/tmp/{file_id}.pdf"
    return FileResponse(
        path=file_path,
        filename=f"document_{file_id}.pdf",
        media_type="application/pdf",
    )
```

### Q4：如何上传文件？

A：使用 `UploadFile`：

```python
from fastapi import UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile):
    contents = await file.read()
    # 处理文件...
    return {"filename": file.filename, "size": len(contents)}
```

---

## 🚀 性能优化

### 后端优化

1. **数据库查询优化**
   ```python
   # ✗ N+1 问题
   users = session.query(User).all()
   for user in users:
       print(user.profile.bio)  # 每个用户查询一次
   
   # ✓ 使用 selectinload
   from sqlalchemy.orm import selectinload
   users = session.query(User).options(
       selectinload(User.profile)
   ).all()
   ```

2. **异步数据库查询**
   ```python
   # 使用 async SQLModel
   async with engine.begin() as conn:
       result = await conn.execute(statement)
   ```

3. **缓存策略**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_config(key: str):
       return session.query(Setting).filter(...).first()
   ```

### 前端优化

1. **组件懒加载**
   ```typescript
   // Vue Router 路由级别代码分割
   const ItemView = defineAsyncComponent(() => import('@/views/items/ItemListView.vue'));
   ```

2. **API 请求优化**
   ```typescript
   // 使用请求防抖
   import { debounce } from 'lodash-es';
   
   const handleSearch = debounce(async (query: string) => {
       const result = await api.searchItems(query);
   }, 300);
   ```

---

## 📖 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
