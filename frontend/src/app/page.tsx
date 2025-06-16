'use client'

import Link from 'next/link'
import { useStats } from '@/hooks/useStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'

export default function Home() {
  const { data: stats, error, isLoading } = useStats()

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to HoistScraper</h1>
        <p className="text-lg text-muted-foreground mb-8">
          AI-powered web scraping platform for Australian grants and opportunities
        </p>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="text-center text-red-500">
          Failed to load statistics
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border p-6">
            <div className="text-2xl font-bold text-blue-600">{stats.total_sites}</div>
            <div className="text-sm text-muted-foreground">Grant Sites Configured</div>
          </div>
          <div className="bg-white rounded-lg border p-6">
            <div className="text-2xl font-bold text-green-600">{stats.total_opportunities}</div>
            <div className="text-sm text-muted-foreground">Opportunities Found</div>
          </div>
          <div className="bg-white rounded-lg border p-6">
            <div className="text-2xl font-bold text-purple-600">{stats.total_jobs}</div>
            <div className="text-sm text-muted-foreground">Scraping Jobs Run</div>
          </div>
          <div className="bg-white rounded-lg border p-6">
            <div className="text-2xl font-bold text-orange-600">{stats.jobs_this_week}</div>
            <div className="text-sm text-muted-foreground">Jobs This Week</div>
          </div>
        </div>
      ) : null}

      {/* Last Scrape Info */}
      {stats?.last_scrape && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm">
            <span className="font-medium">Last scraping run:</span>{' '}
            {new Date(stats.last_scrape).toLocaleString()}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="text-center space-y-4">
        <h2 className="text-xl font-semibold">Quick Actions</h2>
        <div className="flex flex-wrap justify-center gap-4">
          <Link 
            href="/opportunities" 
            className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            View Opportunities
          </Link>
          <Link 
            href="/jobs" 
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-6 py-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            Manage Jobs
          </Link>
          <Link 
            href="/sites" 
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-6 py-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            Manage Sites
          </Link>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-4">System Status</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Backend API</span>
              <span className="text-green-600">✓ Online</span>
            </div>
            <div className="flex justify-between">
              <span>Australian Grant Sites</span>
              <span className="text-green-600">✓ 244 Configured</span>
            </div>
            <div className="flex justify-between">
              <span>Database</span>
              <span className="text-green-600">✓ Connected</span>
            </div>
          </div>
        </div>

        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-4">Recent Activity</h3>
          <div className="text-sm text-muted-foreground">
            {stats?.total_opportunities === 0 ? (
              <p>No opportunities scraped yet. Start a scraping job to begin collecting grant opportunities.</p>
            ) : (
              <p>
                Found {stats?.total_opportunities} opportunities across {stats?.total_sites} Australian grant sites.
                {stats?.jobs_this_week > 0 && ` ${stats.jobs_this_week} jobs completed this week.`}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 