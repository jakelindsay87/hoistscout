'use client'

import { useState } from 'react'
import { Site } from '@/types'
import { SitesDataGrid } from '@/components/sites/SitesDataGrid'
import { AddSitesModal } from '@/components/sites/AddSitesModal'
import { SecretsModal } from '@/components/sites/SecretsModal'

// Mock data for development
const mockSites: Site[] = [
  {
    id: '1',
    name: 'Example Grant Site',
    start_urls: ['https://foo.bar/grants'],
    status: 'active',
    auth: {
      type: 'login_form',
      username_env: 'EX_USER',
      password_env: 'EX_PASS',
      login_url: 'https://foo.bar/login',
      selectors: {
        user: '#u',
        pass: '#p',
        submit: 'button[type=submit]'
      }
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'Public Funding Portal',
    start_urls: ['https://grants.gov/opportunities'],
    status: 'active',
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z'
  },
  {
    id: '3',
    name: 'Research Foundation',
    start_urls: ['https://research-foundation.org/funding'],
    status: 'captcha_blocked',
    created_at: '2024-01-17T10:00:00Z',
    updated_at: '2024-01-17T10:00:00Z'
  },
  {
    id: '4',
    name: 'Tech Innovation Hub',
    start_urls: ['https://techhub.org/competitions'],
    status: 'legal_blocked',
    created_at: '2024-01-18T10:00:00Z',
    updated_at: '2024-01-18T10:00:00Z'
  }
]

export default function SitesPage() {
  const [sites, setSites] = useState<Site[]>(mockSites)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isSecretsModalOpen, setIsSecretsModalOpen] = useState(false)

  const handleAddSites = (newSites: Partial<Site>[]) => {
    const sitesWithIds = newSites.map((site, index) => ({
      ...site,
      id: `new-${Date.now()}-${index}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })) as Site[]
    
    setSites(prev => [...prev, ...sitesWithIds])
    setIsAddModalOpen(false)
  }

  const handleDeleteSite = (siteId: string) => {
    setSites(prev => prev.filter(site => site.id !== siteId))
  }

  const handleUpdateSiteStatus = (siteId: string, status: Site['status']) => {
    setSites(prev => prev.map(site => 
      site.id === siteId 
        ? { ...site, status, updated_at: new Date().toISOString() }
        : site
    ))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sites</h1>
          <p className="text-muted-foreground">
            Manage your crawling targets and authentication settings
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setIsSecretsModalOpen(true)}
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            🔐 Secrets
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Add Sites
          </button>
        </div>
      </div>

      <SitesDataGrid
        sites={sites}
        onDelete={handleDeleteSite}
        onUpdateStatus={handleUpdateSiteStatus}
      />

      <AddSitesModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddSites}
      />

      <SecretsModal
        isOpen={isSecretsModalOpen}
        onClose={() => setIsSecretsModalOpen(false)}
      />
    </div>
  )
} 