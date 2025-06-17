'use client'

import { useState } from 'react'
import { 
  MagnifyingGlassIcon, 
  BellIcon, 
  UserCircleIcon,
  Bars3Icon
} from '@heroicons/react/24/outline'
import { useStats } from '@/hooks/useStats'

export function Header() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data: stats } = useStats()

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Search */}
        <div className="flex items-center flex-1 max-w-lg">
          <div className="relative w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search opportunities, sites, or jobs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Right side - Status & User */}
        <div className="flex items-center space-x-4">
          {/* System Status */}
          {stats && (
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-slate-600">
                  {stats.total_sites} Sites Active
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-slate-600">
                  {stats.total_opportunities} Opportunities
                </span>
              </div>
            </div>
          )}

          {/* Notifications */}
          <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors duration-200">
            <BellIcon className="h-5 w-5" />
          </button>

          {/* User Menu */}
          <div className="flex items-center">
            <button className="flex items-center space-x-2 text-sm text-slate-700 hover:text-slate-900 p-2 rounded-lg hover:bg-slate-50 transition-colors duration-200">
              <UserCircleIcon className="h-6 w-6 text-slate-400" />
              <span className="hidden md:block">Admin</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}