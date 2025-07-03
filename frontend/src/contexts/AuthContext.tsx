'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/apiFetch'

interface User {
  id: string
  email: string
  username: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Check if user is authenticated on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      // Verify token by fetching user info
      const response = await api.get('/api/auth/me')
      setUser(response)
    } catch (error) {
      // Token is invalid or expired
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    try {
      // Create form data for OAuth2 compatibility
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await api.post('/api/auth/login', formData)
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      
      // Get user info
      const userResponse = await api.get('/api/auth/me')
      setUser(userResponse)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }, [router])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    router.push('/login')
  }, [router])

  const refreshToken = useCallback(async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      const response = await api.post('/api/auth/refresh', { refresh_token: refresh })
      localStorage.setItem('access_token', response.access_token)
      
      // Update user info
      await checkAuth()
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      throw error
    }
  }, [logout, checkAuth])

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
    checkAuth
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}