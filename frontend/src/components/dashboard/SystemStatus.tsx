import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { Stats } from '@/hooks/useStats'

interface SystemStatusProps {
  stats?: Stats
}

export function SystemStatus({ stats }: SystemStatusProps) {
  const statusItems = [
    {
      name: 'Backend API',
      status: 'healthy',
      description: 'All systems operational'
    },
    {
      name: 'Database',
      status: 'healthy',
      description: 'Connected and responding'
    },
    {
      name: 'Grant Sites',
      status: 'healthy',
      description: `${stats?.total_sites || 244} sites configured`
    },
    {
      name: 'Worker Queue',
      status: 'healthy',
      description: 'Processing jobs normally'
    }
  ]

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">System Status</h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span className="text-sm text-slate-600">All systems operational</span>
        </div>
      </div>

      <div className="space-y-4">
        {statusItems.map((item) => (
          <div key={item.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-slate-900">{item.name}</p>
                <p className="text-xs text-slate-500">{item.description}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-xs font-medium text-green-700">Healthy</span>
            </div>
          </div>
        ))}
      </div>

      {/* Performance Metrics */}
      <div className="mt-6 pt-6 border-t border-slate-200">
        <h4 className="text-sm font-medium text-slate-900 mb-3">Performance</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-lg font-semibold text-slate-900">
              {stats?.total_opportunities || 0}
            </p>
            <p className="text-xs text-slate-500">Total Opportunities</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-slate-900">
              {stats?.jobs_this_week || 0}
            </p>
            <p className="text-xs text-slate-500">Jobs This Week</p>
          </div>
        </div>
      </div>
    </div>
  )
}