// API configuration with runtime detection and HTTPS enforcement
export function getApiUrl(): string {
  // For production deployment on Render, ALWAYS use HTTPS regardless of env vars
  if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
    // Force HTTPS for any onrender.com deployment
    if (window.location.hostname.includes('hoistscout')) {
      return 'https://hoistscout-api.onrender.com'
    }
    return 'https://hoistscout-api.onrender.com'
  }
  
  // Check environment variable but validate it
  if (process.env.NEXT_PUBLIC_API_URL) {
    const envUrl = process.env.NEXT_PUBLIC_API_URL
    
    // If we're in a browser on HTTPS, force the API URL to be HTTPS too
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
      // Replace http:// with https:// if needed
      if (envUrl.startsWith('http://') && !envUrl.includes('localhost')) {
        console.warn('Upgrading API URL from HTTP to HTTPS for security')
        return envUrl.replace('http://', 'https://')
      }
    }
    
    return envUrl
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
  
  // For any HTTPS page, use HTTPS API
  if (window.location.protocol === 'https:') {
    if (window.location.hostname.includes('hoistscout')) {
      return 'https://hoistscout-api.onrender.com'
    }
    return 'https://hoistscout-api.onrender.com'
  }
  
  // Final fallback
  return 'http://localhost:8000'
}