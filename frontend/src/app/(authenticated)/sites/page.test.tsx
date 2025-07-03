import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { renderWithProviders as render } from '@/test/test-utils'
import SitesPage from './page'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn()
  })
}))

// Mock window.location.href
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000/sites'
  },
  writable: true
})

describe('SitesPage', () => {
  it('should render sites list', async () => {
    render(<SitesPage />)

    // Check loading state
    expect(screen.getByText('Loading...')).toBeInTheDocument()

    // Wait for sites to load
    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument()
    })

    expect(screen.getByText('Test Site')).toBeInTheDocument()
    expect(screen.getByText('https://example.com')).toBeInTheDocument()
    expect(screen.getByText('https://test.com')).toBeInTheDocument()
  })

  it('should handle empty sites list', async () => {
    // Override the default handler before rendering
    server.use(
      http.get('http://localhost:8000/api/websites', () => {
        return HttpResponse.json([])
      })
    )

    render(<SitesPage />)

    // Wait for loading to finish and empty state to appear
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('No sites added yet')).toBeInTheDocument()
  })

  it('should handle API errors', async () => {
    server.use(
      http.get('http://localhost:8000/api/websites', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    render(<SitesPage />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load sites')).toBeInTheDocument()
    })

    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('should add a new site', async () => {
    render(<SitesPage />)

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument()
    })

    // Mock prompt
    window.prompt = vi.fn()
      .mockReturnValueOnce('https://newsite.com')
      .mockReturnValueOnce('New Site')

    // Click add button
    const addButton = screen.getByText('Add Site')
    fireEvent.click(addButton)

    // Wait for the new site to appear
    await waitFor(() => {
      expect(window.prompt).toHaveBeenCalledTimes(2)
    })
  })

  it('should show CSV upload modal', async () => {
    render(<SitesPage />)

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument()
    })

    // Click upload button
    const uploadButton = screen.getByText('Upload CSV')
    fireEvent.click(uploadButton)

    // Check modal appears
    expect(screen.getByText('Upload Sites CSV')).toBeInTheDocument()
    expect(screen.getByText(/Upload a CSV file with columns/)).toBeInTheDocument()
  })

  it('should close CSV upload modal', async () => {
    render(<SitesPage />)

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument()
    })

    // Open modal
    fireEvent.click(screen.getByText('Upload CSV'))
    expect(screen.getByText('Upload Sites CSV')).toBeInTheDocument()

    // Close modal
    fireEvent.click(screen.getByText('Cancel'))
    
    // Modal should be gone
    expect(screen.queryByText('Upload Sites CSV')).not.toBeInTheDocument()
  })
})