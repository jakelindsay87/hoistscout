import { SWRConfiguration } from 'swr'
import { APIError } from '@/lib/apiFetch'

export function useSwrConfig(): SWRConfiguration {
  return {
    // Disable retries for 401 errors to prevent infinite loops
    shouldRetryOnError: (error: Error) => {
      if (error instanceof APIError) {
        // Don't retry client errors (4xx)
        if (error.status >= 400 && error.status < 500) {
          return false
        }
      }
      // Retry server errors (5xx) up to 3 times
      return true
    },
    
    // Configure retry behavior
    errorRetryCount: 3,
    errorRetryInterval: 5000,
    
    // Revalidation settings
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    
    // Error handler
    onError: (error: Error) => {
      if (error instanceof APIError && error.status === 401) {
        // Auth error is handled in apiFetch
        console.log('Authentication required')
      }
    }
  }
}