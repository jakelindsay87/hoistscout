import useSWR, { mutate } from 'swr'
import useSWRMutation from 'swr/mutation'
import { api } from '@/lib/apiFetch'
import { useSwrConfig } from './useSwrConfig'

export interface Website {
  id: number
  url: string
  name?: string
  description?: string
  created_at: string
}

export interface CreateSiteData {
  url: string
  name?: string
  description?: string
}

interface UseSitesOptions {
  page?: number
  limit?: number
}

/**
 * Hook to fetch all sites with optional pagination
 */
export function useSites(options?: UseSitesOptions) {
  const swrConfig = useSwrConfig()
  const params = new URLSearchParams()
  if (options?.page) params.append('page', options.page.toString())
  if (options?.limit) params.append('limit', options.limit.toString())
  
  const queryString = params.toString()
  const url = `/api/websites${queryString ? `?${queryString}` : ''}`

  return useSWR<Website[]>(url, (url: string) => api.get(url), swrConfig)
}

/**
 * Hook to fetch a single site by ID
 */
export function useSite(id: number | string) {
  const swrConfig = useSwrConfig()
  return useSWR<Website>(
    id ? `/api/websites/${id}` : null,
    (url: string) => api.get(url),
    swrConfig
  )
}

/**
 * Hook to create a new site
 */
export function useCreateSite() {
  return useSWRMutation<Website, Error, string, CreateSiteData>(
    '/api/websites',
    async (url, { arg }) => {
      const result = await api.post<Website>(url, arg)
      // Invalidate sites list cache
      await mutate((key) => typeof key === 'string' && key.startsWith('/api/websites'))
      return result
    }
  )
}