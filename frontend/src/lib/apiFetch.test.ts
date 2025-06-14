import { describe, it, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'
import { apiFetch, APIError } from './apiFetch'
import { server } from '@/test/mocks/server'

// Stop MSW for these tests since we're mocking fetch directly
beforeAll(() => server.close())
afterAll(() => server.listen())

// Mock global fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('apiFetch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset environment variables
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('successful requests', () => {
    it('should make a GET request with default options', async () => {
      const mockResponse = { data: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      })

      const result = await apiFetch('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        {
          headers: {
            'Content-Type': 'application/json'
          },
          body: undefined
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should make a POST request with body', async () => {
      const mockResponse = { id: 1, name: 'created' }
      const requestBody = { name: 'test' }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      })

      const result = await apiFetch('/test', {
        method: 'POST',
        body: JSON.stringify(requestBody)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle non-JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => 'plain text response',
        headers: new Headers({ 'content-type': 'text/plain' })
      })

      const result = await apiFetch('/test')
      expect(result).toBe('plain text response')
    })

    it('should handle empty responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers()
      })

      const result = await apiFetch('/test')
      expect(result).toBeNull()
    })
  })

  describe('error handling', () => {
    it('should throw APIError for 4xx errors', async () => {
      const errorResponse = { detail: 'Not found' }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => errorResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      })

      try {
        await apiFetch('/test')
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect(error).toMatchObject({
          status: 404,
          statusText: 'Not Found',
          data: errorResponse
        })
      }
    })

    it('should throw APIError for 5xx errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error',
        headers: new Headers()
      })

      try {
        await apiFetch('/test')
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect(error).toMatchObject({
          status: 500,
          statusText: 'Internal Server Error',
          data: 'Server error'
        })
      }
    })

    it('should throw network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiFetch('/test')).rejects.toThrow('Network error')
    })
  })

  describe('retry logic', () => {
    it('should retry on network errors up to 3 times', async () => {
      const mockResponse = { data: 'success' }
      
      // Fail twice, then succeed
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockResponse,
          headers: new Headers({ 'content-type': 'application/json' })
        })

      const result = await apiFetch('/test', { retries: 3 })

      expect(mockFetch).toHaveBeenCalledTimes(3)
      expect(result).toEqual(mockResponse)
    })

    it('should not retry on 4xx errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ error: 'Invalid input' }),
        headers: new Headers({ 'content-type': 'application/json' })
      })

      await expect(apiFetch('/test', { retries: 3 })).rejects.toThrow(APIError)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('should retry on 5xx errors', async () => {
      const mockResponse = { data: 'success' }
      
      // Fail with 500, then succeed
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
          text: async () => 'Server error',
          headers: new Headers()
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockResponse,
          headers: new Headers({ 'content-type': 'application/json' })
        })

      const result = await apiFetch('/test', { retries: 2 })

      expect(mockFetch).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockResponse)
    })

    it('should throw after all retries are exhausted', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(apiFetch('/test', { retries: 2 })).rejects.toThrow('Network error')
      expect(mockFetch).toHaveBeenCalledTimes(3) // Initial + 2 retries
    })
  })

  describe('request configuration', () => {
    it('should use custom base URL from environment', async () => {
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers({ 'content-type': 'application/json' })
      })

      await apiFetch('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.any(Object)
      )
    })

    it('should merge custom headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers({ 'content-type': 'application/json' })
      })

      await apiFetch('/test', {
        headers: {
          'Authorization': 'Bearer token',
          'X-Custom-Header': 'value'
        }
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token',
            'X-Custom-Header': 'value'
          })
        })
      )
    })

    it('should handle FormData without setting Content-Type', async () => {
      const formData = new FormData()
      formData.append('file', new Blob(['test']), 'test.txt')
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ uploaded: true }),
        headers: new Headers({ 'content-type': 'application/json' })
      })

      await apiFetch('/upload', {
        method: 'POST',
        body: formData
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: formData,
          headers: expect.not.objectContaining({
            'Content-Type': expect.anything()
          })
        })
      )
    })
  })
})