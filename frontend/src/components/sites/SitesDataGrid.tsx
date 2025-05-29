'use client'

import { Site } from '@/types'
import { getStatusColor, getStatusLabel, formatDateTime } from '@/lib/utils'

interface SitesDataGridProps {
  sites: Site[]
  onDelete: (siteId: string) => void
  onUpdateStatus: (siteId: string, status: Site['status']) => void
}

export function SitesDataGrid({ sites, onDelete, onUpdateStatus }: SitesDataGridProps) {
  const handleStatusChange = (siteId: string, newStatus: string) => {
    onUpdateStatus(siteId, newStatus as Site['status'])
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium">URLs</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              <th className="px-4 py-3 text-center text-sm font-medium">Auth</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Last Updated</th>
              <th className="px-4 py-3 text-center text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {sites.map((site) => (
              <tr key={site.id} className="hover:bg-muted/25">
                <td className="px-4 py-3">
                  <div className="font-medium">{site.name}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-muted-foreground">
                    {site.start_urls.slice(0, 2).map((url, index) => (
                      <div key={index} className="truncate max-w-xs">
                        {url}
                      </div>
                    ))}
                    {site.start_urls.length > 2 && (
                      <div className="text-xs text-muted-foreground">
                        +{site.start_urls.length - 2} more
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={site.status}
                    onChange={(e) => handleStatusChange(site.id, e.target.value)}
                    className={`px-2 py-1 rounded-full text-xs font-medium border-0 ${getStatusColor(site.status)}`}
                  >
                    <option value="active">Active</option>
                    <option value="captcha_blocked">CAPTCHA Blocked</option>
                    <option value="legal_blocked">Legal Blocked</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </td>
                <td className="px-4 py-3 text-center">
                  {site.auth ? (
                    <span className="text-lg" title="Authentication configured">
                      🔐
                    </span>
                  ) : (
                    <span className="text-lg text-muted-foreground" title="No authentication">
                      🔓
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">
                  {site.updated_at ? formatDateTime(site.updated_at) : 'Never'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-center space-x-2">
                    <button
                      onClick={() => {
                        // TODO: Implement edit functionality
                        console.log('Edit site:', site.id)
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Are you sure you want to delete "${site.name}"?`)) {
                          onDelete(site.id)
                        }
                      }}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {sites.length === 0 && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">
            <div className="text-4xl mb-4">🌐</div>
            <h3 className="text-lg font-medium mb-2">No sites configured</h3>
            <p className="text-sm">Add your first site to start crawling for opportunities.</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default SitesDataGrid 