"""Centralized permission tree definition.

This module is the single source of truth for RBAC tree metadata.
"""

from typing import TypeAlias

PermissionPageNode: TypeAlias = tuple[str, str, str | None, int, list[str]]
PermissionGroupNode: TypeAlias = tuple[str, str, int, list[PermissionPageNode]]

PERMISSION_TREE: list[PermissionGroupNode] = [
    (
        "内容管理",
        "content",
        10,
        [
            ("物品管理", "items", "/items", 10, ["export"]),
        ],
    ),
    (
        "用户管理",
        "user_mgmt",
        20,
        [
            ("用户列表", "users", "/users", 10, []),
        ],
    ),
    (
        "系统管理",
        "system",
        30,
        [
            ("操作日志", "audit_logs", "/audit-logs", 10, []),
            ("角色权限", "roles", "/roles", 20, []),
            ("配置项管理", "settings", "/settings", 30, []),
            ("定时任务", "jobs", "/jobs", 40, ["trigger", "manage"]),
        ],
    ),
]

BUILTIN_ACTIONS: list[tuple[str, str, bool]] = [
    ("读取", "read", True),
    ("创建", "create", True),
    ("更新", "update", True),
    ("删除", "delete", True),
]
