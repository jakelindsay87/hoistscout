'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  HomeIcon, 
  GlobeAltIcon, 
  BriefcaseIcon, 
  DocumentTextIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ServerIcon
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Opportunities', href: '/opportunities', icon: DocumentTextIcon },
  { name: 'Sites', href: '/sites', icon: GlobeAltIcon },
  { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col">
      {/* Logo */}
      <div className="flex items-center px-6 py-6 border-b border-slate-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
              <ServerIcon className="w-5 h-5 text-white" />
            </div>
          </div>
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-slate-900">HoistScraper</h1>
            <p className="text-xs text-slate-500">Grant Discovery</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={classNames(
                isActive
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                'group flex items-center px-3 py-2 text-sm font-medium border-l-4 rounded-r-md transition-colors duration-200'
              )}
            >
              <item.icon
                className={classNames(
                  isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-500',
                  'mr-3 flex-shrink-0 h-5 w-5 transition-colors duration-200'
                )}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Bottom Section */}
      <div className="px-4 py-4 border-t border-slate-200">
        <div className="flex items-center px-3 py-2">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
              <span className="text-xs font-medium text-slate-600">AU</span>
            </div>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-slate-700">Australia</p>
            <p className="text-xs text-slate-500">244 Grant Sites</p>
          </div>
        </div>
      </div>
    </div>
  )
}