import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePermissionStore } from '@/stores/permission'
import { authRoutes } from './modules/auth'
import { dashboardRoutes } from './modules/dashboard'
import { userRoutes } from './modules/users'
import { itemRoutes } from './modules/items'
import { systemRoutes } from './modules/system'
import { commonRoutes } from './modules/common'

const protectedChildRoutes = [
  ...dashboardRoutes,
  ...userRoutes,
  ...itemRoutes,
  ...systemRoutes,
  ...commonRoutes,
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...authRoutes,
    {
      path: '/',
      component: () => import('@/layouts/AdminLayout.vue'),
      redirect: '/dashboard',
      children: protectedChildRoutes,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

// ── Navigation guards ──────────────────────────────────────────────────────────
router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const permStore = usePermissionStore()

  // Allow public routes (login page)
  if (to.meta.public) return true

  // Not authenticated → redirect to login
  if (!authStore.accessToken) return { name: 'Login' }

  // Ensure user info and navigation are loaded
  if (!authStore.user) {
    await authStore.fetchMe()
    if (!authStore.user) return { name: 'Login' }
  }
  if (permStore.navigation.length === 0) {
    await permStore.loadNavigation()
  }

  // Check route permission
  const requiredPerm = to.meta.permission as string | undefined
  if (requiredPerm && !permStore.hasPermission(requiredPerm)) {
    return { name: 'Forbidden' }
  }

  return true
})

export default router
