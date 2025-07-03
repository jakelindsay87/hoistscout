import { getApiUrl } from '@/config/api'

/**
 * Initialize and log API configuration
 * This helps debug configuration issues in production
 */
export function initApiConfig() {
  if (typeof window !== 'undefined') {
    const apiUrl = getApiUrl()
    const isSecure = window.location.protocol === 'https:'
    const isProduction = window.location.hostname.includes('onrender.com')
    
    // Log configuration in development or if there's a potential issue
    if (process.env.NODE_ENV === 'development' || (isSecure && apiUrl.startsWith('http://'))) {
      console.group('🔧 API Configuration')
      console.log('API URL:', apiUrl)
      console.log('Page Protocol:', window.location.protocol)
      console.log('Page Host:', window.location.hostname)
      console.log('Is Production:', isProduction)
      console.log('Environment:', process.env.NODE_ENV)
      console.log('Configured URL:', process.env.NEXT_PUBLIC_API_URL || 'Not set')
      console.groupEnd()
      
      // Warn about mixed content
      if (isSecure && apiUrl.startsWith('http://') && !apiUrl.includes('localhost')) {
        console.error(
          '⚠️ MIXED CONTENT WARNING: Page is HTTPS but API URL is HTTP. This will be blocked by browsers.'
        )
      }
    }
  }
}

// Auto-initialize when imported
if (typeof window !== 'undefined') {
  initApiConfig()
}