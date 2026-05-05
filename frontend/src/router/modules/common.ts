import type { RouteRecordRaw } from 'vue-router'

export const commonRoutes: RouteRecordRaw[] = [
  {
    path: '403',
    name: 'Forbidden',
    component: () => import('@/views/common/ForbiddenView.vue'),
  },
]
