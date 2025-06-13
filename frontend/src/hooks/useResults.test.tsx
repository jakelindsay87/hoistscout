import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'
import React from 'react'
import { useResult } from './useResults'
import { api } from '@/lib/apiFetch'

// Mock the API module
vi.mock('@/lib/apiFetch', () => ({
  api: {
    get: vi.fn()
  }
}))

// Helper to wrap hooks with SWR provider
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map() }}>
    {children}
  </SWRConfig>
)

describe('useResult', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch job results successfully', async () => {
    const mockResult = {
      jobId: 'job-1',
      websiteId: 1,
      url: 'https://example.com',
      scrapedAt: '2024-01-01T10:00:00',
      data: {
        title: 'Example Website',
        description: 'An example website',
        content: 'Lorem ipsum...'
      }
    }
    
    vi.mocked(api.get).mockResolvedValueOnce(mockResult)

    const { result } = renderHook(() => useResult('job-1'), { wrapper })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockResult)
    expect(api.get).toHaveBeenCalledWith('/api/results/job-1')
  })

  it('should handle errors gracefully', async () => {
    const mockError = new Error('Result not found')
    vi.mocked(api.get).mockRejectedValueOnce(mockError)

    const { result } = renderHook(() => useResult('job-1'), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toBeUndefined()
    expect(result.current.error).toEqual(mockError)
  })

  it('should not fetch if no job id provided', () => {
    renderHook(() => useResult(null), { wrapper })
    expect(api.get).not.toHaveBeenCalled()
  })

  it('should not fetch if job is not completed', () => {
    renderHook(() => useResult('job-1', 'running'), { wrapper })
    expect(api.get).not.toHaveBeenCalled()
  })

  it('should fetch when job status is completed', async () => {
    const mockResult = { data: { title: 'Test' } }
    vi.mocked(api.get).mockResolvedValueOnce(mockResult)

    const { result } = renderHook(() => useResult('job-1', 'completed'), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.get).toHaveBeenCalledWith('/api/results/job-1')
    expect(result.current.data).toEqual(mockResult)
  })
})