import api from '@/api'

export interface SettingPublic {
  id: number
  setting_name: string
  setting_value: string | null
  setting_group: string
  description: string | null
  value_type: 'string' | 'int' | 'bool' | 'json'
  is_sensitive: boolean
  is_encrypted: boolean
  is_readonly: boolean
  created_at: string
  updated_at: string | null
}

export interface SettingsPublic {
  data: SettingPublic[]
  count: number
}

export interface SettingGroupPublic {
  setting_group: string
}

export interface SettingGroupsPublic {
  data: SettingGroupPublic[]
}

export interface SettingListParams {
  setting_name?: string
  setting_group?: string
  is_sensitive?: boolean
  skip?: number
  limit?: number
}

export interface SettingCreate {
  setting_name: string
  setting_value?: string | null
  setting_group: string
  description?: string | null
  value_type?: 'string' | 'int' | 'bool' | 'json'
  is_sensitive?: boolean
  is_encrypted?: boolean
  is_readonly?: boolean
}

export interface SettingUpdate {
  setting_value?: string | null
  setting_group?: string
  description?: string | null
  value_type?: 'string' | 'int' | 'bool' | 'json'
  is_sensitive?: boolean
  is_encrypted?: boolean
  is_readonly?: boolean
}

export const settingsApi = {
  groups: () => api.get<SettingGroupsPublic>('/settings/groups'),

  list: (params?: SettingListParams) =>
    api.get<SettingsPublic>('/settings/', { params }),

  get: (id: number) => api.get<SettingPublic>(`/settings/${id}`),

  create: (data: SettingCreate) => api.post<SettingPublic>('/settings/', data),

  update: (id: number, data: SettingUpdate) =>
    api.patch<SettingPublic>(`/settings/${id}`, data),
}