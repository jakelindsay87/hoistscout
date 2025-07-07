'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Globe, Briefcase, FileText, TrendingUp } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/apiFetch'

interface DashboardStats {
  totalSites: number
  totalOpportunities: number
  activeJobs: number
  recentOpportunities: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalSites: 0,
    totalOpportunities: 0,
    activeJobs: 0,
    recentOpportunities: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      // Fetch stats from multiple endpoints with proper error handling
      const [sitesData, opportunitiesData, jobsData] = await Promise.allSettled([
        api.get('/api/websites'),
        api.get('/api/opportunities'),
        api.get('/api/scraping/jobs')
      ])

      // Handle sites data
      let sites = []
      if (sitesData.status === 'fulfilled' && Array.isArray(sitesData.value)) {
        sites = sitesData.value
      }

      // Handle opportunities data
      let opportunities = []
      if (opportunitiesData.status === 'fulfilled') {
        // Check if response is an array or has a data property
        if (Array.isArray(opportunitiesData.value)) {
          opportunities = opportunitiesData.value
        } else if (opportunitiesData.value?.data && Array.isArray(opportunitiesData.value.data)) {
          opportunities = opportunitiesData.value.data
        } else if (opportunitiesData.value?.opportunities && Array.isArray(opportunitiesData.value.opportunities)) {
          opportunities = opportunitiesData.value.opportunities
        }
      }

      // Handle jobs data
      let jobs = []
      if (jobsData.status === 'fulfilled') {
        if (Array.isArray(jobsData.value)) {
          jobs = jobsData.value
        } else if (jobsData.value?.data && Array.isArray(jobsData.value.data)) {
          jobs = jobsData.value.data
        } else if (jobsData.value?.jobs && Array.isArray(jobsData.value.jobs)) {
          jobs = jobsData.value.jobs
        }
      }

      setStats({
        totalSites: sites.length,
        totalOpportunities: opportunities.length,
        activeJobs: jobs.filter((job: any) => job.status === 'running' || job.status === 'pending').length,
        recentOpportunities: opportunities.filter((opp: any) => {
          if (!opp.created_at) return false
          const createdAt = new Date(opp.created_at)
          const weekAgo = new Date()
          weekAgo.setDate(weekAgo.getDate() - 7)
          return createdAt > weekAgo
        }).length
      })
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error)
      // Set default values on error
      setStats({
        totalSites: 0,
        totalOpportunities: 0,
        activeJobs: 0,
        recentOpportunities: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      title: 'Total Sites',
      value: stats.totalSites,
      description: 'Grant and funding websites',
      icon: Globe,
      href: '/sites',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Opportunities',
      value: stats.totalOpportunities,
      description: 'Total opportunities found',
      icon: FileText,
      href: '/opportunities',
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: 'Active Jobs',
      value: stats.activeJobs,
      description: 'Currently running scrapes',
      icon: Briefcase,
      href: '/jobs',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      title: 'Recent Finds',
      value: stats.recentOpportunities,
      description: 'New in last 7 days',
      icon: TrendingUp,
      href: '/opportunities',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    }
  ]

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your grant discovery platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Link key={stat.title} href={stat.href}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <div className={`${stat.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <CardDescription className="text-xs mt-1">
                    {stat.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link href="/sites">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base">Add New Site</CardTitle>
                <CardDescription>Add a new grant website to monitor</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/jobs">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base">View Active Jobs</CardTitle>
                <CardDescription>Monitor currently running scrape jobs</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/opportunities">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base">Browse Opportunities</CardTitle>
                <CardDescription>View all discovered grant opportunities</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  )
}