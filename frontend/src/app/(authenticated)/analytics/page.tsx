'use client'

import { useState } from 'react'

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d')

  return (
    <div className="px-6 py-6">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Analytics</h1>
          <p className="text-slate-600 mt-1">
            Monitor performance and track grant discovery metrics
          </p>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center space-x-4">
          <span className="text-sm text-slate-600">Time Range:</span>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>

        {/* Coming Soon Message */}
        <div className="bg-white rounded-xl border border-slate-200 p-12">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-semibold text-slate-900">
              Analytics Coming Soon
            </h3>
            <p className="mt-2 text-sm text-slate-600 max-w-md mx-auto">
              We're working on comprehensive analytics to help you track grant discovery performance,
              success rates, and opportunity trends. Check back soon!
            </p>
          </div>
        </div>

        {/* Placeholder Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Total Discoveries', value: '—', change: '—' },
            { label: 'Success Rate', value: '—', change: '—' },
            { label: 'Avg. Processing Time', value: '—', change: '—' },
            { label: 'Active Monitors', value: '—', change: '—' },
          ].map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm"
            >
              <p className="text-sm font-medium text-slate-600">{stat.label}</p>
              <p className="text-2xl font-bold text-slate-900 mt-2">{stat.value}</p>
              <p className="text-xs text-slate-500 mt-1">Change: {stat.change}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}