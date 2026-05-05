import type { RouteRecordRaw } from 'vue-router'

export const systemRoutes: RouteRecordRaw[] = [
  {
    path: 'roles',
    name: 'RolePermission',
    component: () => import('@/views/system/RolePermissionView.vue'),
    meta: { permission: 'system.roles.read' },
  },
  {
    path: 'audit-logs',
    name: 'AuditLog',
    component: () => import('@/views/system/AuditLogListView.vue'),
    meta: { permission: 'system.audit_logs.read' },
  },
]
