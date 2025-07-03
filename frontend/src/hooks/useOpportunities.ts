import useSWR from 'swr'
import useSWRMutation from 'swr/mutation'
import { apiFetch } from '@/lib/apiFetch'
import { useSwrConfig } from './useSwrConfig'

export interface Opportunity {
  id: number
  title: string
  description?: string
  source_url: string
  website_id: number
  job_id: number
  deadline?: string
  amount?: string
  scraped_at: string
}

export interface OpportunityCreate {
  title: string
  description?: string
  source_url: string
  website_id: number
  job_id: number
  deadline?: string
  amount?: string
}

export function useOpportunities() {
  const swrConfig = useSwrConfig();
  return useSWR<Opportunity[]>('/api/opportunities', apiFetch, swrConfig)
}

export function useOpportunity(id: number) {
  const swrConfig = useSwrConfig();
  return useSWR<Opportunity>(`/api/opportunities/${id}`, apiFetch, swrConfig)
}

export function useCreateOpportunity() {
  return useSWRMutation(
    '/api/opportunities',
    async (url: string, { arg }: { arg: OpportunityCreate }) => {
      return apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(arg)
      })
    }
  )
}

export function useDeleteOpportunity() {
  return useSWRMutation(
    '/api/opportunities',
    async (url: string, { arg }: { arg: number }) => {
      return apiFetch(`${url}/${arg}`, {
        method: 'DELETE'
      })
    }
  )
}