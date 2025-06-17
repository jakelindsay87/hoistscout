'use client'

import { useStats } from '@/hooks/useStats'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { ActivityFeed } from '@/components/dashboard/ActivityFeed'
import { SystemStatus } from '@/components/dashboard/SystemStatus'
import { 
  GlobeAltIcon, 
  DocumentTextIcon, 
  BriefcaseIcon, 
  CalendarIcon 
} from '@heroicons/react/24/outline'

export default function Dashboard() {
  const { data: stats, error, isLoading } = useStats()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="text-red-800">
          <h3 className="font-medium">Unable to load dashboard</h3>
          <p className="text-sm mt-1">Failed to connect to the API. Please check your connection and try again.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-1">
          Monitor your Australian grant discovery platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Grant Sites"
          value={stats?.total_sites || 0}
          change={null}
          icon={GlobeAltIcon}
          color="blue"
        />
        <StatsCard
          title="Opportunities"
          value={stats?.total_opportunities || 0}
          change={null}
          icon={DocumentTextIcon}
          color="green"
        />
        <StatsCard
          title="Total Jobs"
          value={stats?.total_jobs || 0}
          change={null}
          icon={BriefcaseIcon}
          color="purple"
        />
        <StatsCard
          title="This Week"
          value={stats?.jobs_this_week || 0}
          change={null}
          icon={CalendarIcon}
          color="orange"
        />
      </div>

      {/* Last Scrape Banner */}
      {stats?.last_scrape && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Last scraping run:</span>{' '}
                {new Date(stats.last_scrape).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column - Quick Actions */}
        <div className="lg:col-span-1">
          <QuickActions />
        </div>

        {/* Right Column - Status & Activity */}
        <div className="lg:col-span-2 space-y-6">
          <SystemStatus stats={stats} />
          <ActivityFeed stats={stats} />
        </div>
      </div>
    </div>
  )
} 