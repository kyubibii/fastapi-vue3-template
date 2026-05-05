import api from '@/api'

export interface UserPublic {
  id: string
  username: string
  nickname: string
  avatar_url: string | null
  email: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
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

export const usersApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<UsersPublic>('/users/', { params }),

  get: (id: string) => api.get<UserPublic>(`/users/${id}`),

  create: (data: UserCreate) => api.post<UserPublic>('/users/', data),

  update: (id: string, data: UserUpdate) =>
    api.patch<UserPublic>(`/users/${id}`, data),

  delete: (id: string) => api.delete(`/users/${id}`),

  assignRoles: (id: string, roleIds: number[]) =>
    api.put(`/users/${id}/roles`, { role_ids: roleIds }),

  getMe: () => api.get<UserPublic>('/users/me'),

  updateMe: (data: UserUpdate) => api.patch<UserPublic>('/users/me', data),

  getNavigation: () => api.get('/users/me/navigation'),
}
