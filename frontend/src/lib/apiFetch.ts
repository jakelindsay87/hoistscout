/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  status: number
  statusText: string
  data: any

  constructor(status: number, statusText: string, data: any) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'APIError'
    this.status = status
    this.statusText = statusText
    this.data = data
  }
}

export interface FetchOptions extends RequestInit {
  retries?: number
  retryDelay?: number
}

/**
 * Enhanced fetch wrapper with error handling and retries
 * @param path - API endpoint path (will be appended to base URL)
 * @param options - Fetch options with additional retry configuration
 * @returns Promise resolving to the response data
 */
export async function apiFetch<T = any>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const {
    retries = 0,
    retryDelay = 1000,
    headers = {},
    body,
    ...fetchOptions
  } = options

  // Get base URL from environment or default
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const url = `${baseUrl}${path}`

  // Setup headers
  const defaultHeaders: HeadersInit = {}
  
  // Only set Content-Type for JSON bodies, not FormData
  if (!(body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json'
  }

  const finalHeaders = {
    ...defaultHeaders,
    ...headers
  }

  // Make the request with retries
  let lastError: Error | null = null
  let attempts = 0
  const maxAttempts = retries + 1

  while (attempts < maxAttempts) {
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers: finalHeaders,
        body: body instanceof FormData || typeof body === 'string' ? body : undefined
      })

      // Handle non-OK responses
      if (!response.ok) {
        let errorData: any
        const contentType = response.headers.get('content-type')
        
        if (contentType?.includes('application/json')) {
          errorData = await response.json()
        } else {
          errorData = await response.text()
        }

        const error = new APIError(response.status, response.statusText, errorData)

        // Don't retry on 4xx errors (client errors)
        if (response.status >= 400 && response.status < 500) {
          throw error
        }

        // Retry on 5xx errors
        lastError = error
        attempts++
        
        if (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempts))
          continue
        }
        
        throw error
      }

      // Handle successful responses
      if (response.status === 204) {
        return null as T
      }

      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return await response.json()
      } else {
        return await response.text() as T
      }

    } catch (error) {
      // Network errors or other fetch errors
      if (error instanceof APIError) {
        throw error
      }

      lastError = error as Error
      attempts++

      if (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempts))
        continue
      }

      throw error
    }
  }

  // This should never be reached, but TypeScript needs it
  throw lastError || new Error('Unknown error')
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  get: <T = any>(path: string, options?: Omit<FetchOptions, 'method'>) =>
    apiFetch<T>(path, { ...options, method: 'GET' }),

  post: <T = any>(path: string, data?: any, options?: Omit<FetchOptions, 'method' | 'body'>) =>
    apiFetch<T>(path, {
      ...options,
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data)
    }),

  put: <T = any>(path: string, data?: any, options?: Omit<FetchOptions, 'method' | 'body'>) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PUT',
      body: data instanceof FormData ? data : JSON.stringify(data)
    }),

  delete: <T = any>(path: string, options?: Omit<FetchOptions, 'method'>) =>
    apiFetch<T>(path, { ...options, method: 'DELETE' })
}