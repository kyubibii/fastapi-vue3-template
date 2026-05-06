import api from '@/api'
import type { UserSearchResults } from '@/api/users'

export interface RolePublic {
  id: number
  name: string
  code: string
  description: string | null
  is_builtin: boolean
}

export interface RolesPublic {
  data: RolePublic[]
  count: number
}

export interface PermissionPublic {
  id: number
  name: string
  code: string
  full_code: string
  is_builtin: boolean
}

export interface PermissionPagePublic {
  id: number
  name: string
  code: string
  page_url: string | null
  sort_order: number
  permissions: PermissionPublic[]
}

export interface PermissionGroupPublic {
  id: number
  name: string
  code: string
  sort_order: number
  pages: PermissionPagePublic[]
}

export interface PermissionTreeResponse {
  groups: PermissionGroupPublic[]
}

export const rolesApi = {
  list: () => api.get<RolesPublic>('/roles/'),
  get: (id: number) => api.get<RolePublic>(`/roles/${id}`),
  create: (data: { name: string; code: string; description?: string }) =>
    api.post<RolePublic>('/roles/', data),
  update: (
    id: number,
    data: { name?: string; description?: string; is_active?: boolean }
  ) => api.patch<RolePublic>(`/roles/${id}`, data),
  delete: (id: number) => api.delete(`/roles/${id}`),
  getPermissions: (id: number) => api.get<number[]>(`/roles/${id}/permissions`),
  assignPermissions: (id: number, permissionIds: number[]) =>
    api.put(`/roles/${id}/permissions`, { permission_ids: permissionIds }),
  getUsers: (id: number, params?: { keyword?: string }) =>
    api.get<UserSearchResults>(`/roles/${id}/users`, { params }),
  assignUsers: (id: number, userIds: string[]) =>
    api.put(`/roles/${id}/users`, { user_ids: userIds }),
}

export const permissionsApi = {
  tree: () => api.get<PermissionTreeResponse>('/permissions/tree'),
}
