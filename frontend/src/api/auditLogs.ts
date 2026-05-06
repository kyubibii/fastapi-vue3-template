import api from '@/api'

export interface AuditLogPublic {
  id: string
  user_id: string | null
  username: string | null
  http_method: string
  endpoint: string
  module: string | null
  operation: string | null
  request_body: string | null
  response_body: string | null
  status_code: number | null
  duration_ms: number | null
  ip_address: string | null
  error_message: string | null
  tags: string | null
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
    module?: string
    endpoint?: string
    start_time?: string
    end_time?: string
    skip?: number
    limit?: number
  }) => api.get<AuditLogsPublic>('/audit-logs/', { params }),
}
