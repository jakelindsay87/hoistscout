import useSWR, { mutate } from 'swr'
import useSWRMutation from 'swr/mutation'
import { api } from '@/lib/apiFetch'

export interface ScrapeJob {
  id: string
  website_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  result_path?: string
  error?: string
}

export interface CreateJobData {
  websiteId: number
}

interface UseJobsOptions {
  websiteId?: number
  status?: ScrapeJob['status']
}

/**
 * Hook to fetch all jobs with optional filtering
 */
export function useJobs(options?: UseJobsOptions) {
  const params = new URLSearchParams()
  if (options?.websiteId) params.append('website_id', options.websiteId.toString())
  if (options?.status) params.append('status', options.status)
  
  const queryString = params.toString()
  const url = `/api/jobs${queryString ? `?${queryString}` : ''}`

  return useSWR<ScrapeJob[]>(
    url,
    (url) => api.get(url),
    {
      refreshInterval: 3000 // Poll every 3 seconds for status updates
    }
  )
}

/**
 * Hook to fetch a single job by ID
 */
export function useJob(id: string | null) {
  return useSWR<ScrapeJob>(
    id ? `/api/jobs/${id}` : null,
    (url) => api.get(url),
    {
      refreshInterval: (data) => {
        // Poll while job is running
        if (data?.status === 'pending' || data?.status === 'running') {
          return 1000 // Poll every second
        }
        return 0 // Stop polling when completed/failed
      }
    }
  )
}

/**
 * Hook to create a new scraping job
 */
export function useCreateJob() {
  return useSWRMutation<ScrapeJob, Error, string, CreateJobData>(
    '/api/scrape',
    async (url, { arg }) => {
      const result = await api.post<ScrapeJob>(`${url}/${arg.websiteId}`)
      // Invalidate jobs list cache
      await mutate((key) => typeof key === 'string' && key.startsWith('/api/jobs'))
      return result
    }
  )
}