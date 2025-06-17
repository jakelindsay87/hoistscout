import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Check if the application is healthy
    // You can add more health checks here (database, external APIs, etc.)
    
    return NextResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'hoistscraper-frontend'
    })
  } catch (error) {
    console.error('Health check failed:', error)
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        service: 'hoistscraper-frontend',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    )
  }
}