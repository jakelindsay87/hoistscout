'use client'

import { useState } from 'react'
import { toast } from '@/components/ui/toast'

interface CredentialsModalProps {
  websiteId: number
  websiteName: string
  onClose: () => void
  onSave: () => void
}

interface CredentialFormData {
  username: string
  password: string
  auth_type: 'basic' | 'form' | 'cookie'
  additional_fields: Record<string, any>
}

export function CredentialsModal({ websiteId, websiteName, onClose, onSave }: CredentialsModalProps) {
  const [formData, setFormData] = useState<CredentialFormData>({
    username: '',
    password: '',
    auth_type: 'basic',
    additional_fields: {}
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.username || !formData.password) {
      toast({
        type: 'error',
        title: 'Missing fields',
        description: 'Username and password are required'
      })
      return
    }

    setIsSubmitting(true)

    try {
      const response = await fetch('/api/credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        },
        body: JSON.stringify({
          website_id: websiteId,
          username: formData.username,
          password: formData.password,
          auth_type: formData.auth_type,
          additional_fields: JSON.stringify(formData.additional_fields)
        })
      })

      if (!response.ok) {
        throw new Error('Failed to save credentials')
      }

      toast({
        type: 'success',
        title: 'Credentials saved',
        description: `Authentication credentials saved for ${websiteName}`
      })

      onSave()
      onClose()
    } catch (error) {
      console.error('Failed to save credentials:', error)
      toast({
        type: 'error',
        title: 'Failed to save credentials',
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderAdditionalFields = () => {
    switch (formData.auth_type) {
      case 'form':
        return (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">Login URL</label>
              <input
                type="url"
                placeholder="https://example.com/login"
                value={formData.additional_fields.login_url || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  additional_fields: {
                    ...formData.additional_fields,
                    login_url: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Username Field Name</label>
              <input
                type="text"
                placeholder="username"
                value={formData.additional_fields.username_field || 'username'}
                onChange={(e) => setFormData({
                  ...formData,
                  additional_fields: {
                    ...formData.additional_fields,
                    username_field: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password Field Name</label>
              <input
                type="text"
                placeholder="password"
                value={formData.additional_fields.password_field || 'password'}
                onChange={(e) => setFormData({
                  ...formData,
                  additional_fields: {
                    ...formData.additional_fields,
                    password_field: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Success Indicator (CSS Selector)</label>
              <input
                type="text"
                placeholder=".dashboard, #user-menu"
                value={formData.additional_fields.success_indicator || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  additional_fields: {
                    ...formData.additional_fields,
                    success_indicator: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500">CSS selector to verify successful login</p>
            </div>
          </>
        )
      
      case 'cookie':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium">Cookie JSON</label>
            <textarea
              placeholder='[{"name": "session", "value": "abc123", "domain": ".example.com"}]'
              value={formData.additional_fields.cookies ? JSON.stringify(formData.additional_fields.cookies) : ''}
              onChange={(e) => {
                try {
                  const cookies = JSON.parse(e.target.value)
                  setFormData({
                    ...formData,
                    additional_fields: {
                      ...formData.additional_fields,
                      cookies
                    }
                  })
                } catch {
                  // Invalid JSON, just store as string
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
            />
            <p className="text-xs text-gray-500">JSON array of cookie objects</p>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Add Credentials</h2>
        <p className="text-gray-600 mb-4">Add authentication credentials for {websiteName}</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Authentication Type</label>
            <select
              value={formData.auth_type}
              onChange={(e) => setFormData({
                ...formData,
                auth_type: e.target.value as 'basic' | 'form' | 'cookie',
                additional_fields: {}
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="basic">Basic Authentication</option>
              <option value="form">Form-based Login</option>
              <option value="cookie">Cookie Authentication</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Username</label>
            <input
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter username"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter password"
            />
          </div>

          {renderAdditionalFields()}

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : 'Save Credentials'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>

        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">
            <strong>Security Note:</strong> Credentials are encrypted before storage using industry-standard encryption.
          </p>
        </div>
      </div>
    </div>
  )
}