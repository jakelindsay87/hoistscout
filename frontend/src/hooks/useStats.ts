import useSWR from 'swr'
import { apiFetch } from '@/lib/apiFetch'

export interface Stats {
  total_sites: number
  total_jobs: number
  total_opportunities: number
  jobs_this_week: number
  last_scrape?: string
}

export function useStats() {
  return useSWR<Stats>('/api/stats', apiFetch)
}