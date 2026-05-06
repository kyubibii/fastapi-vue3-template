import api from '@/api'

export interface JobPublic {
  id: string
  name: string
  description: string
  trigger_type: string
  trigger_description: string
  next_run_time: string | null
  is_paused: boolean
}

export interface JobsPublic {
  data: JobPublic[]
}

export interface JobTriggerResult {
  job_id: string
  message: string
  triggered_at: string
}

export const jobsApi = {
  list: () => api.get<JobsPublic>('/jobs/'),

  trigger: (jobId: string) =>
    api.post<JobTriggerResult>(`/jobs/${jobId}/trigger`),

  pause: (jobId: string) => api.put<JobPublic>(`/jobs/${jobId}/pause`),

  resume: (jobId: string) => api.put<JobPublic>(`/jobs/${jobId}/resume`),
}
