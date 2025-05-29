'use client'

import { useState } from 'react'
import { Site, AddSiteFormData } from '@/types'
import { parseUrls, isValidUrl, extractDomain } from '@/lib/utils'

interface AddSitesModalProps {
  isOpen: boolean
  onClose: () => void
  onAdd: (sites: Partial<Site>[]) => void
}

export function AddSitesModal({ isOpen, onClose, onAdd }: AddSitesModalProps) {
  const [formData, setFormData] = useState<AddSiteFormData>({
    urls: [],
    auth_required: false,
    auth_type: 'login_form'
  })
  const [urlInput, setUrlInput] = useState('')
  const [errors, setErrors] = useState<string[]>([])

  const handleUrlInputChange = (value: string) => {
    setUrlInput(value)
    const urls = parseUrls(value)
    setFormData(prev => ({ ...prev, urls }))
    
    // Validate URLs
    const invalidUrls = value.split('\n')
      .map(line => line.trim())
      .filter(Boolean)
      .filter(line => !isValidUrl(line))
    
    setErrors(invalidUrls.length > 0 ? [`Invalid URLs: ${invalidUrls.join(', ')}`] : [])
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      if (file.name.endsWith('.csv')) {
        // Simple CSV parsing - assumes URLs are in first column
        const lines = text.split('\n').slice(1) // Skip header
        const urls = lines
          .map(line => line.split(',')[0]?.trim())
          .filter(Boolean)
          .filter(isValidUrl)
        
        setUrlInput(urls.join('\n'))
        setFormData(prev => ({ ...prev, urls }))
      } else {
        // Treat as plain text
        handleUrlInputChange(text)
      }
    }
    reader.readAsText(file)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.urls.length === 0) {
      setErrors(['Please enter at least one valid URL'])
      return
    }

    if (errors.length > 0) {
      return
    }

    // Create site objects from URLs
    const sites: Partial<Site>[] = formData.urls.map(url => ({
      name: extractDomain(url),
      start_urls: [url],
      status: 'active' as const,
      auth: formData.auth_required ? {
        type: formData.auth_type!,
        username_env: formData.username_env,
        password_env: formData.password_env,
        login_url: formData.login_url,
        selectors: formData.auth_type === 'login_form' ? {
          user: formData.user_selector || 'input[name="username"]',
          pass: formData.pass_selector || 'input[name="password"]',
          submit: formData.submit_selector || 'button[type="submit"]'
        } : undefined
      } : undefined
    }))

    onAdd(sites)
    
    // Reset form
    setFormData({
      urls: [],
      auth_required: false,
      auth_type: 'login_form'
    })
    setUrlInput('')
    setErrors([])
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Add Sites</h2>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                URLs (one per line or comma-separated)
              </label>
              <textarea
                value={urlInput}
                onChange={(e) => handleUrlInputChange(e.target.value)}
                placeholder="https://example.com/grants&#10;https://another-site.org/opportunities"
                className="w-full h-32 px-3 py-2 border border-input rounded-md resize-none"
                required
              />
              <div className="mt-2">
                <label className="block text-sm text-muted-foreground mb-1">
                  Or upload CSV file:
                </label>
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={handleFileUpload}
                  className="text-sm"
                />
              </div>
            </div>

            {formData.urls.length > 0 && (
              <div className="text-sm text-muted-foreground">
                Found {formData.urls.length} valid URL(s)
              </div>
            )}

            {errors.length > 0 && (
              <div className="text-sm text-red-600">
                {errors.map((error, index) => (
                  <div key={index}>{error}</div>
                ))}
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="auth_required"
                checked={formData.auth_required}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  auth_required: e.target.checked 
                }))}
                className="rounded"
              />
              <label htmlFor="auth_required" className="text-sm font-medium">
                Requires Authentication
              </label>
            </div>

            {formData.auth_required && (
              <div className="space-y-3 pl-6 border-l-2 border-muted">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Authentication Type
                  </label>
                  <select
                    value={formData.auth_type}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      auth_type: e.target.value as 'login_form' | 'basic_auth' | 'api_key'
                    }))}
                    className="w-full px-3 py-2 border border-input rounded-md"
                  >
                    <option value="login_form">Login Form</option>
                    <option value="basic_auth">Basic Auth</option>
                    <option value="api_key">API Key</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Username Env Var
                    </label>
                    <input
                      type="text"
                      value={formData.username_env || ''}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        username_env: e.target.value 
                      }))}
                      placeholder="USERNAME_VAR"
                      className="w-full px-3 py-2 border border-input rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Password Env Var
                    </label>
                    <input
                      type="text"
                      value={formData.password_env || ''}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        password_env: e.target.value 
                      }))}
                      placeholder="PASSWORD_VAR"
                      className="w-full px-3 py-2 border border-input rounded-md"
                    />
                  </div>
                </div>

                {formData.auth_type === 'login_form' && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Login URL (optional)
                    </label>
                    <input
                      type="url"
                      value={formData.login_url || ''}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        login_url: e.target.value 
                      }))}
                      placeholder="https://example.com/login"
                      className="w-full px-3 py-2 border border-input rounded-md"
                    />
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium border border-input rounded-md hover:bg-accent"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={formData.urls.length === 0 || errors.length > 0}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add {formData.urls.length} Site{formData.urls.length !== 1 ? 's' : ''}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// Set it as the default export
export default AddSitesModal 