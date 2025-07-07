'use client'

import { useState } from 'react'
import { useOpportunities, useDeleteOpportunity } from '@/hooks/useOpportunities'
import { useSites } from '@/hooks/useSites'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'

export default function OpportunitiesPage() {
  const { data: opportunities, error, isLoading, mutate } = useOpportunities()
  const { data: sites } = useSites()
  const { trigger: deleteOpportunity, isMutating: isDeleting } = useDeleteOpportunity()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedWebsite, setSelectedWebsite] = useState<string>('')

  // Create website lookup for display
  const websiteMap = new Map(sites?.map(site => [site.id, site]) || [])

  // Filter opportunities
  const filteredOpportunities = opportunities?.filter(opp => {
    const matchesSearch = !searchTerm || 
      opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      opp.description?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesWebsite = !selectedWebsite || 
      opp.website_id.toString() === selectedWebsite
    
    return matchesSearch && matchesWebsite
  }) || []

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return
    
    try {
      await deleteOpportunity(id)
      mutate()
      toast({
        type: 'success',
        title: 'Opportunity deleted',
        description: `Deleted "${title}"`
      })
    } catch (error) {
      console.error('Failed to delete opportunity:', error)
      toast({
        type: 'error',
        title: 'Failed to delete opportunity',
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const exportToCsv = () => {
    if (!opportunities?.length) return
    
    const headers = ['Title', 'Description', 'Source URL', 'Website', 'Deadline', 'Amount', 'Scraped At']
    const csvData = opportunities.map(opp => [
      opp.title,
      opp.description || '',
      opp.source_url,
      websiteMap.get(opp.website_id)?.name || 'Unknown',
      opp.deadline || '',
      opp.amount || '',
      new Date(opp.scraped_at).toLocaleString()
    ])
    
    const csv = [headers, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `opportunities-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
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
        <p className="text-red-500">Failed to load opportunities</p>
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
          <h1 className="text-3xl font-bold">Opportunities</h1>
          <p className="text-muted-foreground">
            {opportunities?.length || 0} scraped opportunities
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={exportToCsv}
            disabled={!opportunities?.length}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search opportunities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <select
            value={selectedWebsite}
            onChange={(e) => setSelectedWebsite(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All websites</option>
            {sites?.map(site => (
              <option key={site.id} value={site.id.toString()}>
                {site.name || site.url}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Opportunities table */}
      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-4 text-left font-medium">Title</th>
              <th className="p-4 text-left font-medium">Website</th>
              <th className="p-4 text-left font-medium">Amount</th>
              <th className="p-4 text-left font-medium">Deadline</th>
              <th className="p-4 text-left font-medium">Scraped</th>
              <th className="p-4 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredOpportunities.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  {opportunities?.length === 0 
                    ? "No opportunities found yet. Run a scraping job to find opportunities." 
                    : "No opportunities match your filters."}
                </td>
              </tr>
            ) : (
              filteredOpportunities.map((opportunity) => (
                <tr key={opportunity.id} className="border-b">
                  <td className="p-4">
                    <div>
                      <div className="font-medium">{opportunity.title}</div>
                      {opportunity.description && (
                        <div className="text-sm text-muted-foreground mt-1">
                          {opportunity.description.length > 100 
                            ? `${opportunity.description.substring(0, 100)}...`
                            : opportunity.description}
                        </div>
                      )}
                      <a 
                        href={opportunity.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-blue-500 hover:text-blue-700 mt-1 inline-block"
                      >
                        View source
                      </a>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm">
                      {websiteMap.get(opportunity.website_id)?.name || 'Unknown'}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm">
                      {opportunity.amount || '-'}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm">
                      {opportunity.deadline 
                        ? new Date(opportunity.deadline).toLocaleDateString()
                        : '-'}
                    </div>
                  </td>
                  <td className="p-4 text-muted-foreground">
                    <div className="text-sm">
                      {new Date(opportunity.scraped_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(opportunity.id, opportunity.title)}
                      disabled={isDeleting}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
} 