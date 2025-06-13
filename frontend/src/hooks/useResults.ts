import useSWR from 'swr'
import { api } from '@/lib/apiFetch'
import { ScrapeJob } from './useJobs'

export interface ScrapeResult {
  jobId: string
  websiteId: number
  url: string
  scrapedAt: string
  data: Record<string, any>
}

/**
 * Hook to fetch scraping results for a completed job
 * @param jobId - The job ID to fetch results for
 * @param jobStatus - Optional job status to prevent fetching if not completed
 */
export function useResult(jobId: string | null, jobStatus?: ScrapeJob['status']) {
  // Only fetch if we have a job ID and it's completed (or status not provided)
  const shouldFetch = jobId && (!jobStatus || jobStatus === 'completed')
  
  return useSWR<ScrapeResult>(
    shouldFetch ? `/api/results/${jobId}` : null,
    (url: string) => api.get(url)
  )
}