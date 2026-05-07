import api from '@/api'

export interface DictionaryTypePublic {
  id: string
  type_code: string
  type_name: string
  description: string | null
  sort_order: number
  created_at: string
  updated_at: string | null
}

export interface DictionaryTypesPublic {
  data: DictionaryTypePublic[]
  count: number
}

export interface DictionaryTypeListParams {
  type_code?: string
  type_name?: string
  skip?: number
  limit?: number
}

export interface DictionaryTypeCreate {
  type_code: string
  type_name: string
  description?: string | null
  sort_order?: number
}

export interface DictionaryTypeUpdate {
  type_code?: string
  type_name?: string
  description?: string | null
  sort_order?: number
}

export interface DictionaryItemPublic {
  id: string
  type_id: string
  item_code: string
  item_label: string
  item_value: string
  sort_order: number
  enabled: boolean
  created_at: string
  updated_at: string | null
}

export interface DictionaryItemsPublic {
  data: DictionaryItemPublic[]
  count: number
}

export interface DictionaryItemListParams {
  type_id?: string
  item_code?: string
  item_label?: string
  enabled?: boolean
  skip?: number
  limit?: number
}

export interface DictionaryItemCreate {
  type_id: string
  item_code: string
  item_label: string
  item_value: string
  sort_order?: number
  enabled?: boolean
}

export interface DictionaryItemUpdate {
  type_id?: string
  item_code?: string
  item_label?: string
  item_value?: string
  sort_order?: number
  enabled?: boolean
}

export interface DictionaryOptionItemPublic {
  code: string
  label: string
  value: string
  sort_order: number
}

export interface DictionaryOptionsPublic {
  type_code: string
  data: DictionaryOptionItemPublic[]
}

export const dictionaryApi = {
  listTypes: (params?: DictionaryTypeListParams) =>
    api.get<DictionaryTypesPublic>('/dictionaries/', { params }),

  getType: (id: string) => api.get<DictionaryTypePublic>(`/dictionaries/${id}`),

  createType: (data: DictionaryTypeCreate) =>
    api.post<DictionaryTypePublic>('/dictionaries/', data),

  updateType: (id: string, data: DictionaryTypeUpdate) =>
    api.patch<DictionaryTypePublic>(`/dictionaries/${id}`, data),

  deleteType: (id: string) => api.delete(`/dictionaries/${id}`),

  listItems: (params?: DictionaryItemListParams) =>
    api.get<DictionaryItemsPublic>('/dictionary-items/', { params }),

  getItem: (id: string) => api.get<DictionaryItemPublic>(`/dictionary-items/${id}`),

  createItem: (data: DictionaryItemCreate) =>
    api.post<DictionaryItemPublic>('/dictionary-items/', data),

  updateItem: (id: string, data: DictionaryItemUpdate) =>
    api.patch<DictionaryItemPublic>(`/dictionary-items/${id}`, data),

  deleteItem: (id: string) => api.delete(`/dictionary-items/${id}`),

  getEnabledItemsByTypeCode: (typeCode: string) =>
    api.get<DictionaryOptionsPublic>(`/dictionaries/by-code/${typeCode}/items`),
}
