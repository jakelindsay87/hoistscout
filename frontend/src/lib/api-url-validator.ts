/**
 * Validates and corrects API URLs to ensure HTTPS is used in production
 * This is a safety net to catch any configuration issues
 */
export function validateApiUrl(url: string): string {
  // Only run in browser
  if (typeof window === 'undefined') {
    return url
  }
  
  // If the current page is HTTPS and the API URL is HTTP (not localhost)
  if (
    window.location.protocol === 'https:' &&
    url.startsWith('http://') &&
    !url.includes('localhost') &&
    !url.includes('127.0.0.1')
  ) {
    console.error(
      `SECURITY WARNING: Attempting to use HTTP API (${url}) from HTTPS page. Upgrading to HTTPS.`
    )
    
    // Log additional debug info
    console.debug('Debug info:', {
      pageProtocol: window.location.protocol,
      pageHost: window.location.hostname,
      apiUrl: url,
      env: process.env.NODE_ENV,
      configuredUrl: process.env.NEXT_PUBLIC_API_URL
    })
    
    // Force HTTPS
    return url.replace('http://', 'https://')
  }
  
  return url
}