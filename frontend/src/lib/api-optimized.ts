"""Optimized API client with request batching and caching."""
import { cache } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Request deduplication and caching
const requestCache = new Map<string, Promise<any>>()
const CACHE_TTL = 5000 // 5 seconds

// Optimized fetch with retries and caching
export const apiFetch = cache(async (
  endpoint: string,
  options?: RequestInit & { skipCache?: boolean }
): Promise<any> => {
  const url = `${API_URL}${endpoint}`
  const cacheKey = `${options?.method || 'GET'}:${url}:${JSON.stringify(options?.body || {})}`
  
  // Check cache for GET requests
  if (!options?.skipCache && (options?.method || 'GET') === 'GET') {
    const cached = requestCache.get(cacheKey)
    if (cached) {
      return cached
    }
  }
  
  // Create request promise
  const requestPromise = fetchWithRetry(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  }).then(async (response) => {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  })
  
  // Cache GET requests
  if (!options?.skipCache && (options?.method || 'GET') === 'GET') {
    requestCache.set(cacheKey, requestPromise)
    
    // Clear cache after TTL
    setTimeout(() => {
      requestCache.delete(cacheKey)
    }, CACHE_TTL)
  }
  
  return requestPromise
})

// Fetch with exponential backoff retry
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 3,
  backoff = 1000
): Promise<Response> {
  try {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(30000), // 30 second timeout
    })
    
    // Retry on 5xx errors
    if (response.status >= 500 && retries > 0) {
      await new Promise(resolve => setTimeout(resolve, backoff))
      return fetchWithRetry(url, options, retries - 1, backoff * 2)
    }
    
    return response
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, backoff))
      return fetchWithRetry(url, options, retries - 1, backoff * 2)
    }
    throw error
  }
}

// Batch multiple API requests
export async function batchRequests<T>(
  requests: Array<{ endpoint: string; options?: RequestInit }>
): Promise<T[]> {
  const promises = requests.map(({ endpoint, options }) =>
    apiFetch(endpoint, options)
  )
  
  return Promise.all(promises)
}

// Optimized API methods
export const api = {
  // Websites
  websites: {
    list: (params?: { skip?: number; limit?: number; active_only?: boolean }) =>
      apiFetch(`/api/websites?${new URLSearchParams(params as any)}`),
    
    get: (id: number) => apiFetch(`/api/websites/${id}`),
    
    create: (data: any) =>
      apiFetch('/api/websites', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    update: (id: number, data: any) =>
      apiFetch(`/api/websites/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    
    delete: (id: number) =>
      apiFetch(`/api/websites/${id}`, {
        method: 'DELETE',
      }),
  },
  
  // Scrape Jobs
  jobs: {
    list: (params?: { skip?: number; limit?: number; status?: string }) =>
      apiFetch(`/api/scrape-jobs?${new URLSearchParams(params as any)}`),
    
    get: (id: number) => apiFetch(`/api/scrape-jobs/${id}`),
    
    create: (websiteId: number) =>
      apiFetch('/api/scrape-jobs', {
        method: 'POST',
        body: JSON.stringify({ website_id: websiteId }),
      }),
    
    stats: () => apiFetch('/api/scrape-jobs/stats'),
  },
  
  // Opportunities
  opportunities: {
    list: (params?: { 
      skip?: number; 
      limit?: number; 
      website_id?: number;
      search?: string;
      deadline_after?: string;
    }) => apiFetch(`/api/opportunities?${new URLSearchParams(params as any)}`),
    
    export: (format: 'json' | 'csv', websiteId?: number) => {
      const params = new URLSearchParams({ format })
      if (websiteId) params.append('website_id', websiteId.toString())
      return apiFetch(`/api/opportunities/export?${params}`)
    },
  },
  
  // Health
  health: () => apiFetch('/health', { skipCache: true }),
}

// Prefetch data for better performance
export function prefetchData() {
  // Prefetch common data
  api.websites.list({ limit: 20 })
  api.jobs.stats()
}

// WebSocket connection for real-time updates (if implemented)
export class RealtimeConnection {
  private ws: WebSocket | null = null
  private reconnectInterval: number = 5000
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  
  constructor(private url: string) {}
  
  connect(onMessage: (data: any) => void) {
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (error) {
          console.error('WebSocket message parse error:', error)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.reconnect(onMessage)
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
      this.reconnect(onMessage)
    }
  }
  
  private reconnect(onMessage: (data: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
      
      setTimeout(() => {
        this.connect(onMessage)
      }, this.reconnectInterval * this.reconnectAttempts)
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
  
  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}