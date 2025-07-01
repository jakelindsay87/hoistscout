"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  PlayCircle, PauseCircle, CheckCircle, XCircle, 
  Clock, Globe, FileText, AlertCircle, RefreshCw 
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

interface JobDetails {
  id: string
  website_id: string
  website_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  priority: 'low' | 'medium' | 'high'
  progress: {
    current: number
    total: number
    stage: string
    percentage: number
  }
  metrics: {
    pages_processed: number
    opportunities_found: number
    documents_downloaded: number
    errors_count: number
    processing_time: number
  }
  started_at?: string
  completed_at?: string
  error_message?: string
}

interface JobProgressTrackerProps {
  websocketUrl?: string
}

export function JobProgressTracker({ websocketUrl = 'ws://localhost:8000/ws/jobs' }: JobProgressTrackerProps) {
  const [jobs, setJobs] = useState<JobDetails[]>([])
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const wsRef = React.useRef<WebSocket | null>(null)

  useEffect(() => {
    // Initial fetch
    fetchJobs()

    // WebSocket connection for real-time updates
    if (autoRefresh) {
      wsRef.current = new WebSocket(websocketUrl)
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'job_update') {
            updateJob(data.job)
          } else if (data.type === 'job_list') {
            setJobs(data.jobs)
          }
        } catch (error) {
          console.error('Failed to parse job update:', error)
        }
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [websocketUrl, autoRefresh])

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/jobs?status=active')
      const data = await response.json()
      setJobs(data)
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    }
  }

  const updateJob = (updatedJob: JobDetails) => {
    setJobs(prev => {
      const index = prev.findIndex(job => job.id === updatedJob.id)
      if (index !== -1) {
        const newJobs = [...prev]
        newJobs[index] = updatedJob
        return newJobs
      } else {
        return [updatedJob, ...prev]
      }
    })
  }

  const getStatusIcon = (status: JobDetails['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />
      case 'running':
        return <PlayCircle className="h-4 w-4 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <XCircle className="h-4 w-4" />
      case 'cancelled':
        return <PauseCircle className="h-4 w-4" />
      default:
        return null
    }
  }

  const getStatusColor = (status: JobDetails['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-500'
      case 'running':
        return 'bg-blue-500'
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'cancelled':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getPriorityColor = (priority: JobDetails['priority']) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500'
      case 'medium':
        return 'bg-yellow-500'
      case 'low':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
    }
  }

  const activeJobs = jobs.filter(job => ['pending', 'running'].includes(job.status))
  const completedJobs = jobs.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status))

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Job Progress Tracker</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                {activeJobs.length} Active
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchJobs}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Active Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeJobs.map(job => (
                <div
                  key={job.id}
                  className="p-4 rounded-lg border bg-card cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => setSelectedJob(job.id === selectedJob ? null : job.id)}
                >
                  <div className="space-y-3">
                    {/* Job Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(job.status)}
                        <span className="font-medium">{job.website_name}</span>
                        <Badge className={getPriorityColor(job.priority)} variant="secondary">
                          {job.priority}
                        </Badge>
                      </div>
                      <Badge className={getStatusColor(job.status)} variant="secondary">
                        {job.status}
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    {job.status === 'running' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{job.progress.stage}</span>
                          <span className="font-mono">{job.progress.percentage}%</span>
                        </div>
                        <Progress value={job.progress.percentage} className="h-2" />
                      </div>
                    )}

                    {/* Metrics */}
                    <div className="grid grid-cols-4 gap-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Globe className="h-3 w-3 text-muted-foreground" />
                        <span>{job.metrics.pages_processed} pages</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FileText className="h-3 w-3 text-muted-foreground" />
                        <span>{job.metrics.opportunities_found} opps</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FileText className="h-3 w-3 text-muted-foreground" />
                        <span>{job.metrics.documents_downloaded} docs</span>
                      </div>
                      {job.metrics.errors_count > 0 && (
                        <div className="flex items-center gap-1 text-red-500">
                          <AlertCircle className="h-3 w-3" />
                          <span>{job.metrics.errors_count} errors</span>
                        </div>
                      )}
                    </div>

                    {/* Expanded Details */}
                    {selectedJob === job.id && (
                      <div className="mt-3 pt-3 border-t space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Job ID</span>
                          <span className="font-mono">{job.id.slice(0, 8)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Started</span>
                          <span>
                            {job.started_at 
                              ? formatDistanceToNow(new Date(job.started_at), { addSuffix: true })
                              : 'Not started'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Processing Time</span>
                          <span>{job.metrics.processing_time}s</span>
                        </div>
                        {job.error_message && (
                          <div className="mt-2 p-2 rounded bg-red-500/10 text-red-500 text-xs">
                            {job.error_message}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completed Jobs */}
      {completedJobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Completed Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {completedJobs.slice(0, 10).map(job => (
                  <div
                    key={job.id}
                    className="p-3 rounded-lg border bg-card"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(job.status)}
                        <span className="text-sm">{job.website_name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{job.metrics.opportunities_found} opportunities</span>
                        <span>•</span>
                        <span>
                          {job.completed_at 
                            ? format(new Date(job.completed_at), 'HH:mm')
                            : 'Unknown'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}