import type { RouteRecordRaw } from 'vue-router'

export const userRoutes: RouteRecordRaw[] = [
  {
    path: 'users',
    name: 'UserList',
    component: () => import('@/views/users/UserListView.vue'),
    meta: { permission: 'user_mgmt.users.read' },
  },
  {
    path: 'users/create',
    name: 'UserCreate',
    component: () => import('@/views/users/UserFormView.vue'),
    meta: { permission: 'user_mgmt.users.create' },
  },
  {
    path: 'users/:id/edit',
    name: 'UserEdit',
    component: () => import('@/views/users/UserFormView.vue'),
    meta: { permission: 'user_mgmt.users.update' },
  },
]
