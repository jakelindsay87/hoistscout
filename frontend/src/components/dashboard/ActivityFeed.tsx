import { ClockIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import { Stats } from '@/hooks/useStats'

interface ActivityFeedProps {
  stats?: Stats
}

export function ActivityFeed({ stats }: ActivityFeedProps) {
  // Mock recent activity - in a real app, this would come from an API
  const activities = [
    {
      id: 1,
      type: 'scrape_completed',
      title: 'Scraping job completed',
      description: 'Found 3 new opportunities from Australian Government Grants',
      timestamp: stats?.last_scrape || new Date().toISOString(),
      status: 'success'
    },
    {
      id: 2,
      type: 'site_added',
      title: 'New site configured',
      description: 'Added Innovation Australia to grant sites',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      status: 'info'
    },
    {
      id: 3,
      type: 'scrape_started',
      title: 'Bulk scraping initiated',
      description: 'Started scraping all 244 Australian grant sites',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      status: 'pending'
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />
      case 'error':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-600" />
      default:
        return <ClockIcon className="w-5 h-5 text-blue-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffMs = now.getTime() - time.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffMs / (1000 * 60))

    if (diffHours > 0) {
      return `${diffHours}h ago`
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`
    } else {
      return 'Just now'
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Recent Activity</h3>
        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
          View all
        </button>
      </div>

      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div 
            key={activity.id} 
            className={`flex items-start space-x-3 p-3 rounded-lg border ${getStatusColor(activity.status)}`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getStatusIcon(activity.status)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900">
                {activity.title}
              </p>
              <p className="text-sm text-slate-600 mt-1">
                {activity.description}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {formatTimeAgo(activity.timestamp)}
              </p>
            </div>
          </div>
        ))}
      </div>

      {!stats?.total_opportunities && (
        <div className="mt-6 pt-6 border-t border-slate-200">
          <div className="text-center">
            <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <ClockIcon className="w-6 h-6 text-slate-400" />
            </div>
            <h4 className="text-sm font-medium text-slate-900 mb-1">
              No scraping activity yet
            </h4>
            <p className="text-xs text-slate-500">
              Start your first scraping job to see activity here
            </p>
          </div>
        </div>
      )}
    </div>
  )
}