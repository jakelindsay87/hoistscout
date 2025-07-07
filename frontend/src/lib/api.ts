import { API_BASE_URL } from './config'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// Custom fetch implementation to handle authentication properly
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token')
  
  const headers = new Headers(options.headers || {})
  
  // Ensure proper header format
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  // Set default content type if not already set
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Include cookies for CORS
  })
  
  return response
}

export const api = {
  async get(endpoint: string) {
    const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new ApiError(response.status, error)
    }
    
    return response.json()
  },

  async post(endpoint: string, data?: any) {
    const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new ApiError(response.status, error)
    }
    
    return response.json()
  },

  async put(endpoint: string, data: any) {
    const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new ApiError(response.status, error)
    }
    
    return response.json()
  },

  async delete(endpoint: string) {
    const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new ApiError(response.status, error)
    }
    
    return response.status === 204 ? null : response.json()
  },

  // Special method for form data (login)
  async postForm(endpoint: string, data: Record<string, string>) {
    const formData = new URLSearchParams()
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value)
    })
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new ApiError(response.status, error)
    }
    
    return response.json()
  },
}

// Auth-specific functions
export const auth = {
  async login(username: string, password: string) {
    const response = await api.postForm('/api/auth/login', {
      username,
      password,
      grant_type: 'password',
    })
    
    // Store token
    if (response.access_token) {
      localStorage.setItem('token', response.access_token)
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token)
      }
    }
    
    return response
  },

  async logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  },

  async getMe() {
    return api.get('/api/auth/me')
  },

  isAuthenticated() {
    return !!localStorage.getItem('token')
  },
}