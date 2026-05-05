import api from '@/api'

export interface AuditLogPublic {
  id: string
  user_id: string | null
  username: string | null
  http_method: string
  endpoint: string
  status_code: number
  duration_ms: number
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AuditLogsPublic {
  data: AuditLogPublic[]
  count: number
}

export const auditLogsApi = {
  list: (params?: {
    user_id?: string
    endpoint?: string
    start_time?: string
    end_time?: string
    skip?: number
    limit?: number
  }) => api.get<AuditLogsPublic>('/audit-logs/', { params }),
}
