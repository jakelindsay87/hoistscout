'use client'

import { useState } from 'react'
import { useSites, useCreateSite } from '@/hooks/useSites'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'
import Papa from 'papaparse'

export default function SitesPage() {
  const { data: sites, error, isLoading, mutate } = useSites()
  const { trigger: createSite, isMutating: isCreating } = useCreateSite()
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadProgress('Parsing CSV...')

    Papa.parse(file, {
      header: true,
      complete: async (results) => {
        const data = results.data as any[]
        const validSites = data.filter(row => row.url && row.url.trim())
        
        setUploadProgress(`Uploading ${validSites.length} sites...`)
        
        try {
          // Create sites one by one (we could batch this in the future)
          let created = 0
          for (const site of validSites) {
            await createSite({
              url: site.url.trim(),
              name: site.name?.trim(),
              description: site.description?.trim()
            })
            created++
            setUploadProgress(`Uploaded ${created}/${validSites.length} sites...`)
          }
          
          setUploadProgress(null)
          setIsUploadModalOpen(false)
          // Reset file input
          event.target.value = ''
          // Refresh the sites list
          mutate()
          toast({
            type: 'success',
            title: 'Sites uploaded successfully',
            description: `Uploaded ${created} sites from CSV`
          })
        } catch (error) {
          console.error('Failed to upload sites:', error)
          setUploadProgress(null)
          toast({
            type: 'error',
            title: 'Upload failed',
            description: 'Failed to upload sites from CSV'
          })
        }
      },
      error: (error) => {
        console.error('Failed to parse CSV:', error)
        setUploadProgress('Error parsing CSV file')
        setTimeout(() => setUploadProgress(null), 3000)
      }
    })
  }

  const handleAddSite = async () => {
    const url = prompt('Enter website URL:')
    if (!url) return
    
    const name = prompt('Enter website name (optional):') || undefined
    
    try {
      await createSite({ url, name })
      mutate()
      toast({
        type: 'success',
        title: 'Site added',
        description: `Added ${name || url}`
      })
    } catch (error) {
      console.error('Failed to create site:', error)
      toast({
        type: 'error',
        title: 'Failed to add site',
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500">Failed to load sites</p>
        <button 
          onClick={() => mutate()}
          className="mt-4 text-sm text-blue-500 hover:text-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sites</h1>
          <p className="text-muted-foreground">
            Manage websites for scraping
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => setIsUploadModalOpen(true)}
            disabled={isCreating}
          >
            Upload CSV
          </Button>
          <Button
            onClick={handleAddSite}
            disabled={isCreating}
          >
            Add Site
          </Button>
        </div>
      </div>

      {/* Simple table view */}
      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-4 text-left font-medium">URL</th>
              <th className="p-4 text-left font-medium">Name</th>
              <th className="p-4 text-left font-medium">Created</th>
              <th className="p-4 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sites?.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-8 text-center text-muted-foreground">
                  No sites added yet
                </td>
              </tr>
            ) : (
              sites?.map((site) => (
                <tr key={site.id} className="border-b">
                  <td className="p-4">
                    <a 
                      href={site.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:text-blue-700"
                    >
                      {site.url}
                    </a>
                  </td>
                  <td className="p-4">{site.name || '-'}</td>
                  <td className="p-4 text-muted-foreground">
                    {new Date(site.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Navigate to jobs page filtered by site
                        window.location.href = `/jobs?site=${site.id}`
                      }}
                    >
                      View Jobs
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Upload modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Upload Sites CSV</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Upload a CSV file with columns: url, name (optional), description (optional)
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="mb-4 w-full"
              disabled={!!uploadProgress}
            />
            {uploadProgress && (
              <p className="text-sm text-blue-500 mb-4">{uploadProgress}</p>
            )}
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => {
                  setIsUploadModalOpen(false)
                  setUploadProgress(null)
                }}
                disabled={!!uploadProgress}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}