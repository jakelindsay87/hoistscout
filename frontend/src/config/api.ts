// API configuration with runtime detection
export function getApiUrl(): string {
  // Check environment variable first
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // Server-side: always use HTTPS for production
  if (typeof window === 'undefined') {
    return process.env.NODE_ENV === 'production' 
      ? 'https://hoistscout-api.onrender.com'
      : 'http://localhost:8000'
  }
  
  // Client-side: detect based on current location
  const isLocalhost = window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1'
  
  if (isLocalhost) {
    return 'http://localhost:8000'
  }
  
  // For production, always use HTTPS
  if (window.location.protocol === 'https:') {
    if (window.location.hostname.includes('hoistscout')) {
      return 'https://hoistscout-api.onrender.com'
    }
    return 'https://hoistscraper.onrender.com'
  }
  
  // Fallback
  return 'http://localhost:8000'
}