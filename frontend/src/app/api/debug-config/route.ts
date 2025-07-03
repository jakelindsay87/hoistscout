import { NextResponse } from 'next/server'
import { headers } from 'next/headers'

export async function GET() {
  const headersList = headers()
  
  // Collect all configuration information
  const debugInfo = {
    timestamp: new Date().toISOString(),
    environment: {
      NODE_ENV: process.env.NODE_ENV,
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
      VERCEL_URL: process.env.VERCEL_URL,
      PORT: process.env.PORT,
    },
    runtime: {
      isServer: typeof window === 'undefined',
      platform: process.platform,
      nodeVersion: process.version,
    },
    request: {
      host: headersList.get('host'),
      protocol: headersList.get('x-forwarded-proto') || 'http',
      userAgent: headersList.get('user-agent'),
    },
    apiUrlDetection: {
      fromEnv: process.env.NEXT_PUBLIC_API_URL || 'NOT SET',
      shouldBeHttps: (headersList.get('x-forwarded-proto') || 'http') === 'https',
      computedUrl: (() => {
        if (process.env.NEXT_PUBLIC_API_URL) {
          return process.env.NEXT_PUBLIC_API_URL
        }
        const host = headersList.get('host') || ''
        if (host.includes('hoistscout')) {
          return 'https://hoistscout-api.onrender.com'
        }
        return 'https://hoistscraper.onrender.com'
      })(),
    },
    buildInfo: {
      buildTime: process.env.BUILD_TIME || 'unknown',
      buildId: process.env.BUILD_ID || 'unknown',
    }
  }
  
  return NextResponse.json(debugInfo, {
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate',
    }
  })
}