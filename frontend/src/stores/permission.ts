import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'

export interface NavPermission {
  id: number
  name: string
  code: string
  full_code: string
}

export interface NavPage {
  id: number
  name: string
  code: string
  page_url: string | null
  sort_order: number
  permissions: NavPermission[]
}

export interface NavGroup {
  id: number
  name: string
  code: string
  sort_order: number
  pages: NavPage[]
}

export const usePermissionStore = defineStore('permission', () => {
  const navigation = ref<NavGroup[]>([])
  const permissionCodes = ref<Set<string>>(new Set())

  async function loadNavigation(): Promise<void> {
    const response = await usersApi.getNavigation()
    navigation.value = response.data.groups ?? []
    // Flatten all permission codes for fast lookup
    const codes = new Set<string>()
    for (const group of navigation.value) {
      for (const page of group.pages) {
        for (const perm of page.permissions) {
          codes.add(perm.full_code)
        }
      }
    }
    permissionCodes.value = codes
  }

  function hasPermission(code: string): boolean {
    // Wildcard — superuser
    if (permissionCodes.value.has('*')) return true
    return permissionCodes.value.has(code)
  }

  function clearNavigation(): void {
    navigation.value = []
    permissionCodes.value = new Set()
  }

  return {
    navigation,
    permissionCodes,
    loadNavigation,
    hasPermission,
    clearNavigation,
  }
})
