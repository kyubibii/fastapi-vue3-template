import api from '@/api'

export interface RoleOptionPublic {
  id: number
  name: string
}

export interface UserPublic {
  id: string
  username: string
  nickname: string
  avatar_url: string | null
  email: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  roles: RoleOptionPublic[]
}

export interface UsersPublic {
  data: UserPublic[]
  count: number
}

export interface UserCreate {
  username: string
  nickname: string
  password: string
  email?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface UserUpdate {
  nickname?: string
  email?: string
  password?: string
  is_active?: boolean
  is_superuser?: boolean
  avatar_url?: string
}

export interface UserListParams {
  username?: string
  email?: string
  is_active?: boolean
  role_ids?: number[]
  skip?: number
  limit?: number
}

export interface UserSearchPublic {
  id: string
  username: string
  nickname: string
  email: string | null
  roles: RoleOptionPublic[]
}

export interface UserSearchResults {
  data: UserSearchPublic[]
}

export const usersApi = {
  list: (params?: UserListParams) =>
    api.get<UsersPublic>('/users/', { params }),

  get: (id: string) => api.get<UserPublic>(`/users/${id}`),

  create: (data: UserCreate) => api.post<UserPublic>('/users/', data),

  update: (id: string, data: UserUpdate) =>
    api.patch<UserPublic>(`/users/${id}`, data),

  delete: (id: string) => api.delete(`/users/${id}`),

  assignRoles: (id: string, roleIds: number[]) =>
    api.put(`/users/${id}/roles`, { role_ids: roleIds }),

  search: (params?: { keyword?: string; exclude_role_id?: number; limit?: number }) =>
    api.get<UserSearchResults>('/users/search', { params }),

  getMe: () => api.get<UserPublic>('/users/me'),

  updateMe: (data: UserUpdate) => api.patch<UserPublic>('/users/me', data),

  getNavigation: () => api.get('/users/me/navigation'),
}
