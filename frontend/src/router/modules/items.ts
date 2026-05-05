import type { RouteRecordRaw } from 'vue-router'

export const itemRoutes: RouteRecordRaw[] = [
  {
    path: 'items',
    name: 'ItemList',
    component: () => import('@/views/items/ItemListView.vue'),
    meta: { permission: 'content.items.read' },
  },
  {
    path: 'items/create',
    name: 'ItemCreate',
    component: () => import('@/views/items/ItemFormView.vue'),
    meta: { permission: 'content.items.create' },
  },
  {
    path: 'items/:id/edit',
    name: 'ItemEdit',
    component: () => import('@/views/items/ItemFormView.vue'),
    meta: { permission: 'content.items.update' },
  },
]
