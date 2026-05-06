import api from '@/api'

export interface ItemPublic {
  id: string
  title: string
  description: string | null
  owner_id: string
  created_at: string
}

export interface ItemsPublic {
  data: ItemPublic[]
  count: number
}

export interface ItemListParams {
  title?: string
  skip?: number
  limit?: number
}

export interface ItemCreate {
  title: string
  description?: string
}

export interface ItemUpdate {
  title?: string
  description?: string
}

export const itemsApi = {
  list: (params?: ItemListParams) =>
    api.get<ItemsPublic>('/items/', { params }),

  get: (id: string) => api.get<ItemPublic>(`/items/${id}`),

  create: (data: ItemCreate) => api.post<ItemPublic>('/items/', data),

  update: (id: string, data: ItemUpdate) =>
    api.patch<ItemPublic>(`/items/${id}`, data),

  delete: (id: string) => api.delete(`/items/${id}`),

  exportCsv: (params?: Pick<ItemListParams, 'title'>) =>
    api.get('/items/export/csv', { params, responseType: 'blob' }),
}
