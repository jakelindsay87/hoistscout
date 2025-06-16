'use client'

import { useSearchParams } from 'next/navigation'
import { useMemo, Suspense } from 'react'
import { useJobs, useCreateJob } from '@/hooks/useJobs'
import { useSites } from '@/hooks/useSites'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'

function JobsPageContent() {
  const searchParams = useSearchParams()
  const siteId = searchParams.get('site')
  
  const { data: jobs, error, isLoading } = useJobs(
    siteId ? { websiteId: parseInt(siteId) } : undefined
  )
  const { data: sites } = useSites()
  const { trigger: createJob, isMutating: isCreating } = useCreateJob()

  // Map site IDs to names for display
  const siteMap = useMemo(() => {
    if (!sites) return {}
    return sites.reduce((acc, site) => {
      acc[site.id] = site
      return acc
    }, {} as Record<number, typeof sites[0]>)
  }, [sites])

  const handleRunScrape = async (websiteId: number) => {
    try {
      await createJob({ websiteId })
      toast({
        type: 'success',
        title: 'Job created',
        description: `Scraping job has been queued`
      })
    } catch (error) {
      console.error('Failed to create job:', error)
      toast({
        type: 'error',
        title: 'Failed to create job',
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || ''}`}>
        {status}
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500">Failed to load jobs</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-4 text-sm text-blue-500 hover:text-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Monitor scraping job status
            {siteId && siteMap[parseInt(siteId)] && (
              <span> for {siteMap[parseInt(siteId)].name || siteMap[parseInt(siteId)].url}</span>
            )}
          </p>
        </div>
        {siteId && (
          <Button
            onClick={() => handleRunScrape(parseInt(siteId))}
            disabled={isCreating}
          >
            {isCreating ? 'Creating...' : 'Run Scrape'}
          </Button>
        )}
      </div>

      {/* Jobs table */}
      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-4 text-left font-medium">Job ID</th>
              <th className="p-4 text-left font-medium">Website</th>
              <th className="p-4 text-left font-medium">Status</th>
              <th className="p-4 text-left font-medium">Started</th>
              <th className="p-4 text-left font-medium">Completed</th>
              <th className="p-4 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs?.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  No jobs found
                </td>
              </tr>
            ) : (
              jobs?.map((job) => (
                <tr key={job.id} className="border-b">
                  <td className="p-4 font-mono text-sm">{job.id}</td>
                  <td className="p-4">
                    {siteMap[job.website_id] ? (
                      <a 
                        href={`/sites?id=${job.website_id}`}
                        className="text-blue-500 hover:text-blue-700"
                      >
                        {siteMap[job.website_id].name || siteMap[job.website_id].url}
                      </a>
                    ) : (
                      `Site ${job.website_id}`
                    )}
                  </td>
                  <td className="p-4">{getStatusBadge(job.status)}</td>
                  <td className="p-4 text-muted-foreground">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-4 text-muted-foreground">
                    {job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-4 text-right">
                    {job.status === 'completed' && job.raw_data ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          window.location.href = `/opportunities?job=${job.id}`
                        }}
                      >
                        View Results
                      </Button>
                    ) : job.status === 'failed' && job.error_message ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => alert(`Error: ${job.error_message}`)}
                      >
                        View Error
                      </Button>
                    ) : (
                      <span className="text-muted-foreground text-sm">
                        {job.status === 'running' ? 'In Progress...' : 'Pending...'}
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Quick actions for sites without filtered view */}
      {!siteId && sites && sites.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sites.map((site) => (
              <div key={site.id} className="border rounded-lg p-4">
                <h3 className="font-medium mb-2">{site.name || site.url}</h3>
                <p className="text-sm text-muted-foreground mb-3 truncate">{site.url}</p>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.location.href = `/jobs?site=${site.id}`}
                  >
                    View Jobs
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleRunScrape(site.id)}
                    disabled={isCreating}
                  >
                    Run Scrape
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function JobsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    }>
      <JobsPageContent />
    </Suspense>
  )
}