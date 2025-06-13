'use client'

import { useSearchParams } from 'next/navigation'
import { useJob } from '@/hooks/useJobs'
import { useResult } from '@/hooks/useResults'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

export default function ResultsPage() {
  const searchParams = useSearchParams()
  const jobId = searchParams.get('job')
  const [isExpanded, setIsExpanded] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  
  const { data: job } = useJob(jobId)
  const { data: result, error, isLoading } = useResult(jobId, job?.status)

  const handleDownload = () => {
    if (!result) return
    
    const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${jobId}-results.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const renderJson = (data: any, path = ''): JSX.Element => {
    if (data === null) return <span className="text-gray-500">null</span>
    if (data === undefined) return <span className="text-gray-500">undefined</span>
    
    if (typeof data !== 'object') {
      const strValue = String(data)
      const highlighted = searchTerm && strValue.toLowerCase().includes(searchTerm.toLowerCase())
      return (
        <span className={highlighted ? 'bg-yellow-200' : ''}>
          {typeof data === 'string' ? `"${data}"` : strValue}
        </span>
      )
    }

    if (Array.isArray(data)) {
      return (
        <span>
          [
          {data.length > 0 && (
            <>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-blue-500 hover:text-blue-700 mx-1 text-xs"
              >
                {isExpanded ? '−' : '+'}
              </button>
              {isExpanded && (
                <div className="ml-4">
                  {data.map((item, index) => (
                    <div key={index}>
                      {renderJson(item, `${path}[${index}]`)}
                      {index < data.length - 1 && ','}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          ]
        </span>
      )
    }

    const entries = Object.entries(data)
    return (
      <span>
        {'{'}
        {entries.length > 0 && (
          <>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-500 hover:text-blue-700 mx-1 text-xs"
            >
              {isExpanded ? '−' : '+'}
            </button>
            {isExpanded && (
              <div className="ml-4">
                {entries.map(([key, value], index) => (
                  <div key={key}>
                    <span className="text-blue-600">"{key}"</span>: {renderJson(value, `${path}.${key}`)}
                    {index < entries.length - 1 && ','}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
        {'}'}
      </span>
    )
  }

  if (!jobId) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No job ID provided</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => window.location.href = '/jobs'}
        >
          Go to Jobs
        </Button>
      </div>
    )
  }

  if (isLoading || (job && job.status !== 'completed' && !result)) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <LoadingSpinner />
        <p className="mt-4 text-muted-foreground">
          {job?.status === 'running' ? 'Job is still running...' : 'Loading results...'}
        </p>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500">
          {job?.status === 'failed' ? 'Job failed' : 'Failed to load results'}
        </p>
        {job?.error && (
          <p className="mt-2 text-sm text-muted-foreground">{job.error}</p>
        )}
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => window.location.href = '/jobs'}
        >
          Back to Jobs
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Results</h1>
          <p className="text-muted-foreground">
            Job {jobId} • Scraped at {new Date(result.scrapedAt).toLocaleString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => window.location.href = '/jobs'}
          >
            Back to Jobs
          </Button>
          <Button onClick={handleDownload}>
            Download JSON
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex items-center space-x-2">
        <input
          type="text"
          placeholder="Search in JSON..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-md"
        />
        <Button
          variant="outline"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Collapse All' : 'Expand All'}
        </Button>
      </div>

      {/* JSON viewer */}
      <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-[600px]">
        <pre className="text-sm font-mono">
          {renderJson(result.data)}
        </pre>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-medium">URL:</span>{' '}
          <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
            {result.url}
          </a>
        </div>
        <div>
          <span className="font-medium">Website ID:</span> {result.websiteId}
        </div>
      </div>
    </div>
  )
}