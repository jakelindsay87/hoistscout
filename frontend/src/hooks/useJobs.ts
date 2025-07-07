import useSWR, { mutate } from 'swr'
import useSWRMutation from 'swr/mutation'
import { apiFetch } from '@/lib/apiFetch'
import { useSwrConfig } from './useSwrConfig'

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
  const swrConfig = useSwrConfig();
  return useSWR<ScrapeJob[]>(
    '/api/scraping/jobs',
    apiFetch,
    {
      ...swrConfig,
      refreshInterval: 3000 // Poll every 3 seconds for status updates
    }
  )
}

/**
 * Hook to fetch a single job by ID
 */
export function useJob(id: number | null) {
  const swrConfig = useSwrConfig();
  return useSWR<ScrapeJob>(
    id ? `/api/scraping/jobs/${id}` : null,
    apiFetch,
    {
      ...swrConfig,
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
  return useSWRMutation<ScrapeJob, Error, string, { websiteId: number }>(
    '/api/scraping/jobs',
    async (url, { arg }) => {
      // Convert frontend format to backend format
      const jobData = {
        website_id: arg.websiteId,
        job_type: 'full', // Default to full scrape
        priority: 5 // Default priority
      }
      
      const result = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData)
      })
      // Invalidate jobs list cache
      await mutate((key) => typeof key === 'string' && key.startsWith('/api/scraping/jobs'))
      return result
    }
  )
}