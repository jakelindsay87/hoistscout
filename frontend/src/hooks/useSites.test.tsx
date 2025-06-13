import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig, mutate } from 'swr'
import React from 'react'
import { useSites, useCreateSite } from './useSites'
import { api } from '@/lib/apiFetch'

// Mock the API module
vi.mock('@/lib/apiFetch', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Mock SWR mutate
vi.mock('swr', async () => {
  const actual = await vi.importActual('swr')
  return {
    ...actual,
    mutate: vi.fn()
  }
})

// Helper to wrap hooks with SWR provider
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map() }}>
    {children}
  </SWRConfig>
)

describe('useSites', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should fetch sites successfully', async () => {
    const mockSites = [
      { id: 1, url: 'https://example.com', name: 'Example', created_at: '2024-01-01' },
      { id: 2, url: 'https://test.com', name: 'Test', created_at: '2024-01-02' }
    ]

    vi.mocked(api.get).mockResolvedValueOnce(mockSites)

    const { result } = renderHook(() => useSites(), { wrapper })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()
    expect(result.current.error).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockSites)
    expect(result.current.error).toBeUndefined()
    expect(api.get).toHaveBeenCalledWith('/api/sites')
  })

  it('should handle errors gracefully', async () => {
    const mockError = new Error('Failed to fetch')
    vi.mocked(api.get).mockRejectedValueOnce(mockError)

    const { result } = renderHook(() => useSites(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toBeUndefined()
    expect(result.current.error).toEqual(mockError)
  })

  it('should support pagination', async () => {
    const mockSites = [{ id: 1, url: 'https://example.com' }]
    vi.mocked(api.get).mockResolvedValueOnce(mockSites)

    const { result } = renderHook(() => useSites({ page: 2, limit: 10 }), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.get).toHaveBeenCalledWith('/api/sites?page=2&limit=10')
  })
})

describe('useCreateSite', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a site successfully', async () => {
    const newSite = { id: 3, url: 'https://new.com', name: 'New Site' }
    const siteData = { url: 'https://new.com', name: 'New Site' }
    
    vi.mocked(api.post).mockResolvedValueOnce(newSite)

    const { result } = renderHook(() => useCreateSite(), { wrapper })

    expect(result.current.isMutating).toBe(false)
    expect(result.current.error).toBeUndefined()

    // Trigger mutation
    let createdSite
    await waitFor(async () => {
      createdSite = await result.current.trigger(siteData)
    })

    expect(api.post).toHaveBeenCalledWith('/api/sites', siteData)
    expect(createdSite).toEqual(newSite)
  })

  it('should handle creation errors', async () => {
    const error = new Error('Failed to create')
    vi.mocked(api.post).mockRejectedValueOnce(error)

    const { result } = renderHook(() => useCreateSite(), { wrapper })

    await waitFor(async () => {
      try {
        await result.current.trigger({ url: 'invalid' })
      } catch (e) {
        // Expected to throw
      }
    })

    expect(result.current.error).toEqual(error)
  })

  it('should invalidate sites list on successful creation', async () => {
    const newSite = { id: 3, url: 'https://new.com' }
    vi.mocked(api.post).mockResolvedValueOnce(newSite)
    vi.mocked(mutate).mockClear()

    const { result } = renderHook(() => useCreateSite(), { wrapper })

    await waitFor(async () => {
      await result.current.trigger({ url: 'https://new.com' })
    })

    // Check that it invalidates the sites cache
    expect(mutate).toHaveBeenCalled()
  })
})