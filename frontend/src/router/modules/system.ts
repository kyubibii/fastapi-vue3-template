import type { RouteRecordRaw } from 'vue-router'

export const systemRoutes: RouteRecordRaw[] = [
  {
    path: 'dictionaries',
    name: 'DictionaryManagement',
    component: () => import('@/views/system/DictionaryManagementView.vue'),
    meta: { permission: 'system.dictionaries.read' },
  },
  {
    path: 'settings',
    name: 'SettingManagement',
    component: () => import('@/views/system/SettingManagementView.vue'),
    meta: { permission: 'system.settings.read' },
  },
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
  {
    path: 'jobs',
    name: 'JobManagement',
    component: () => import('@/views/system/JobManagementView.vue'),
    meta: { permission: 'system.jobs.read' },
  },
]
