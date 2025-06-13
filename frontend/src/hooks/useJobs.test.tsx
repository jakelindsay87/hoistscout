import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'
import React from 'react'
import { useJobs, useJob, useCreateJob } from './useJobs'
import { api } from '@/lib/apiFetch'

// Mock the API module
vi.mock('@/lib/apiFetch', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Helper to wrap hooks with SWR provider
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map() }}>
    {children}
  </SWRConfig>
)

describe('useJobs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch jobs successfully', async () => {
    const mockJobs = [
      { 
        id: 'job-1', 
        website_id: 1, 
        status: 'completed',
        started_at: '2024-01-01T10:00:00',
        completed_at: '2024-01-01T10:05:00',
        result_path: '/data/job-1.json'
      },
      { 
        id: 'job-2', 
        website_id: 2, 
        status: 'running',
        started_at: '2024-01-01T10:10:00'
      }
    ]

    vi.mocked(api.get).mockResolvedValueOnce(mockJobs)

    const { result } = renderHook(() => useJobs(), { wrapper })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockJobs)
    expect(api.get).toHaveBeenCalledWith('/api/jobs')
  })

  it('should filter jobs by website', async () => {
    const mockJobs = [{ id: 'job-1', website_id: 1, status: 'completed' }]
    vi.mocked(api.get).mockResolvedValueOnce(mockJobs)

    const { result } = renderHook(() => useJobs({ websiteId: 1 }), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.get).toHaveBeenCalledWith('/api/jobs?website_id=1')
  })

  it('should filter jobs by status', async () => {
    const mockJobs = [{ id: 'job-1', status: 'running' }]
    vi.mocked(api.get).mockResolvedValueOnce(mockJobs)

    const { result } = renderHook(() => useJobs({ status: 'running' }), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.get).toHaveBeenCalledWith('/api/jobs?status=running')
  })
})

describe('useJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch a single job', async () => {
    const mockJob = { 
      id: 'job-1', 
      website_id: 1, 
      status: 'completed',
      result_path: '/data/job-1.json'
    }
    
    vi.mocked(api.get).mockResolvedValueOnce(mockJob)

    const { result } = renderHook(() => useJob('job-1'), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockJob)
    expect(api.get).toHaveBeenCalledWith('/api/jobs/job-1')
  })

  it('should not fetch if no id provided', () => {
    renderHook(() => useJob(null), { wrapper })
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useCreateJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a job successfully', async () => {
    const newJob = { id: 'job-3', website_id: 1, status: 'pending' }
    
    vi.mocked(api.post).mockResolvedValueOnce(newJob)

    const { result } = renderHook(() => useCreateJob(), { wrapper })

    expect(result.current.isMutating).toBe(false)

    // Trigger mutation
    let createdJob
    await waitFor(async () => {
      createdJob = await result.current.trigger({ websiteId: 1 })
    })

    expect(api.post).toHaveBeenCalledWith('/api/scrape/1')
    expect(createdJob).toEqual(newJob)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create job')
    vi.mocked(api.post).mockRejectedValueOnce(error)

    const { result } = renderHook(() => useCreateJob(), { wrapper })

    await waitFor(async () => {
      try {
        await result.current.trigger({ websiteId: 1 })
      } catch (e) {
        // Expected to throw
      }
    })

    expect(result.current.error).toEqual(error)
  })
})