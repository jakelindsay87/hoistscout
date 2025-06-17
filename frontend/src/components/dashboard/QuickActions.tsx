import Link from 'next/link'
import { 
  DocumentTextIcon, 
  BriefcaseIcon, 
  GlobeAltIcon,
  PlusIcon,
  PlayIcon
} from '@heroicons/react/24/outline'

const actions = [
  {
    name: 'View Opportunities',
    description: 'Browse discovered grants',
    href: '/opportunities',
    icon: DocumentTextIcon,
    color: 'bg-blue-600 hover:bg-blue-700'
  },
  {
    name: 'Manage Jobs',
    description: 'Monitor scraping jobs',
    href: '/jobs',
    icon: BriefcaseIcon,
    color: 'bg-purple-600 hover:bg-purple-700'
  },
  {
    name: 'Configure Sites',
    description: 'Manage grant websites',
    href: '/sites',
    icon: GlobeAltIcon,
    color: 'bg-green-600 hover:bg-green-700'
  }
]

export function QuickActions() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Quick Actions</h3>
        <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center">
          <PlayIcon className="w-4 h-4 text-slate-600" />
        </div>
      </div>

      <div className="space-y-3">
        {actions.map((action) => (
          <Link
            key={action.name}
            href={action.href}
            className="group flex items-center p-3 rounded-lg border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all duration-200"
          >
            <div className={`flex-shrink-0 p-2 rounded-lg ${action.color} group-hover:scale-105 transition-transform duration-200`}>
              <action.icon className="w-4 h-4 text-white" />
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-slate-900 group-hover:text-slate-700">
                {action.name}
              </p>
              <p className="text-xs text-slate-500">
                {action.description}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Start Button */}
      <div className="mt-6 pt-6 border-t border-slate-200">
        <Link
          href="/jobs"
          className="flex items-center justify-center w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-sm hover:shadow-md"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Start New Scraping Job
        </Link>
      </div>
    </div>
  )
}