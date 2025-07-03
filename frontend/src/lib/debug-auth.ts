/**
 * Advanced authentication debugging utilities
 */

export function setupAuthDebugger() {
  if (typeof window === 'undefined') return

  // Log all API requests
  const originalFetch = window.fetch
  window.fetch = async (...args) => {
    const [url, options] = args
    
    console.group(`🔍 API Request: ${options?.method || 'GET'} ${url}`)
    console.log('Headers:', options?.headers)
    console.log('Auth Token:', localStorage.getItem('access_token')?.substring(0, 20) + '...')
    console.groupEnd()
    
    try {
      const response = await originalFetch(...args)
      
      if (response.status === 401) {
        console.error(`❌ 401 Unauthorized: ${url}`)
        console.log('Response headers:', Object.fromEntries(response.headers.entries()))
      }
      
      return response
    } catch (error) {
      console.error(`🔥 Network error: ${url}`, error)
      throw error
    }
  }

  // Monitor localStorage changes
  const originalSetItem = localStorage.setItem
  localStorage.setItem = function(key, value) {
    if (key === 'access_token' || key === 'refresh_token') {
      console.log(`🔐 Token stored: ${key} = ${value.substring(0, 20)}...`)
    }
    return originalSetItem.call(this, key, value)
  }

  const originalRemoveItem = localStorage.removeItem
  localStorage.removeItem = function(key) {
    if (key === 'access_token' || key === 'refresh_token') {
      console.log(`🗑️ Token removed: ${key}`)
    }
    return originalRemoveItem.call(this, key)
  }

  console.log('🐛 Auth debugger enabled')
}

// Auto-enable in development
if (process.env.NODE_ENV === 'development') {
  setupAuthDebugger()
}