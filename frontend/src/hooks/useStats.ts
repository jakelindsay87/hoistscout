import useSWR from 'swr'
import { apiFetch } from '@/lib/apiFetch'
import { useSwrConfig } from './useSwrConfig'

export interface Stats {
  total_sites: number
  total_jobs: number
  total_opportunities: number
  jobs_this_week: number
  last_scrape?: string
}

export function useStats() {
  const swrConfig = useSwrConfig();
  return useSWR<Stats>('/api/stats', apiFetch, swrConfig)
}