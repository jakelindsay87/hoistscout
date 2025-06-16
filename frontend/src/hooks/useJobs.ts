import useSWR, { mutate } from 'swr'
import useSWRMutation from 'swr/mutation'
import { apiFetch } from '@/lib/apiFetch'

export interface ScrapeJob {
  id: number
  website_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
  raw_data?: string
  created_at: string
  updated_at: string
}

export interface CreateJobData {
  website_id: number
}

interface UseJobsOptions {
  websiteId?: number
  status?: ScrapeJob['status']
}

/**
 * Hook to fetch all jobs with optional filtering
 */
export function useJobs(options?: UseJobsOptions) {
  return useSWR<ScrapeJob[]>(
    '/api/scrape-jobs',
    apiFetch,
    {
      refreshInterval: 3000 // Poll every 3 seconds for status updates
    }
  )
}

/**
 * Hook to fetch a single job by ID
 */
export function useJob(id: number | null) {
  return useSWR<ScrapeJob>(
    id ? `/api/scrape-jobs/${id}` : null,
    apiFetch,
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
    '/api/scrape-jobs',
    async (url, { arg }) => {
      const result = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(arg)
      })
      // Invalidate jobs list cache
      await mutate((key) => typeof key === 'string' && key.startsWith('/api/scrape-jobs'))
      return result
    }
  )
}