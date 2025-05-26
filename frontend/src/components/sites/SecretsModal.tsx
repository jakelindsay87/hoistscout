'use client'

import { useState } from 'react'
import { SecretConfig } from '@/types'

interface SecretsModalProps {
  isOpen: boolean
  onClose: () => void
}

// Mock secrets configuration
const mockSecrets: SecretConfig[] = [
  {
    name: 'Example Site Username',
    env_var_name: 'EX_USER',
    description: 'Username for Example Grant Site login',
    required: true
  },
  {
    name: 'Example Site Password',
    env_var_name: 'EX_PASS',
    description: 'Password for Example Grant Site login',
    required: true
  },
  {
    name: 'Academic Portal Username',
    env_var_name: 'ACADEMIC_USER',
    description: 'Username for Academic Opportunities portal',
    required: true
  },
  {
    name: 'Academic Portal Password',
    env_var_name: 'ACADEMIC_PASS',
    description: 'Password for Academic Opportunities portal',
    required: true
  },
  {
    name: 'Proxy URLs',
    env_var_name: 'PROXY_URLS',
    description: 'Comma-separated list of proxy server URLs',
    required: false
  }
]

export function SecretsModal({ isOpen, onClose }: SecretsModalProps) {
  const [secrets, setSecrets] = useState<SecretConfig[]>(mockSecrets)
  const [newSecret, setNewSecret] = useState<Partial<SecretConfig>>({
    name: '',
    env_var_name: '',
    description: '',
    required: false
  })
  const [isAdding, setIsAdding] = useState(false)

  const handleAddSecret = () => {
    if (!newSecret.name || !newSecret.env_var_name) {
      return
    }

    const secret: SecretConfig = {
      name: newSecret.name,
      env_var_name: newSecret.env_var_name.toUpperCase(),
      description: newSecret.description,
      required: newSecret.required || false
    }

    setSecrets(prev => [...prev, secret])
    setNewSecret({
      name: '',
      env_var_name: '',
      description: '',
      required: false
    })
    setIsAdding(false)
  }

  const handleDeleteSecret = (envVarName: string) => {
    setSecrets(prev => prev.filter(secret => secret.env_var_name !== envVarName))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold">Environment Variables</h2>
              <p className="text-sm text-muted-foreground">
                Configure environment variable names. Values are set in your deployment platform (e.g., Render dashboard).
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Environment Variable</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
                    <th className="px-4 py-3 text-center text-sm font-medium">Required</th>
                    <th className="px-4 py-3 text-center text-sm font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {secrets.map((secret) => (
                    <tr key={secret.env_var_name} className="hover:bg-muted/25">
                      <td className="px-4 py-3 font-medium">{secret.name}</td>
                      <td className="px-4 py-3">
                        <code className="px-2 py-1 bg-muted rounded text-sm">
                          {secret.env_var_name}
                        </code>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {secret.description || 'No description'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {secret.required ? (
                          <span className="text-red-600 font-medium">Required</span>
                        ) : (
                          <span className="text-muted-foreground">Optional</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleDeleteSecret(secret.env_var_name)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                  
                  {isAdding && (
                    <tr className="bg-muted/25">
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={newSecret.name || ''}
                          onChange={(e) => setNewSecret(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="Secret name"
                          className="w-full px-2 py-1 border border-input rounded text-sm"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={newSecret.env_var_name || ''}
                          onChange={(e) => setNewSecret(prev => ({ 
                            ...prev, 
                            env_var_name: e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_')
                          }))}
                          placeholder="ENV_VAR_NAME"
                          className="w-full px-2 py-1 border border-input rounded text-sm font-mono"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={newSecret.description || ''}
                          onChange={(e) => setNewSecret(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="Description (optional)"
                          className="w-full px-2 py-1 border border-input rounded text-sm"
                        />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={newSecret.required || false}
                          onChange={(e) => setNewSecret(prev => ({ ...prev, required: e.target.checked }))}
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-3 text-center space-x-2">
                        <button
                          onClick={handleAddSecret}
                          className="text-sm text-green-600 hover:text-green-800"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => {
                            setIsAdding(false)
                            setNewSecret({
                              name: '',
                              env_var_name: '',
                              description: '',
                              required: false
                            })
                          }}
                          className="text-sm text-gray-600 hover:text-gray-800"
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {!isAdding && (
              <button
                onClick={() => setIsAdding(true)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                Add Environment Variable
              </button>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">💡 Deployment Instructions</h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>
                  <strong>For Render:</strong> Go to your service dashboard → Environment tab → Add the environment variables listed above with their actual values.
                </p>
                <p>
                  <strong>For Docker:</strong> Use <code className="bg-blue-100 px-1 rounded">-e VAR_NAME=value</code> or add to your <code className="bg-blue-100 px-1 rounded">.env</code> file.
                </p>
                <p>
                  <strong>Security:</strong> Never commit actual secret values to your repository. Only store the variable names here.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium border border-input rounded-md hover:bg-accent"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 