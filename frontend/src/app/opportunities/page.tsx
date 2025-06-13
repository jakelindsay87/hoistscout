'use client'

import React, { useState, useMemo, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Opportunity } from '@/types'
import { formatDate, truncateText } from '../../lib/utils'

// Mock data for development
const mockOpportunities: Opportunity[] = [
  {
    id: '1',
    title: 'AI Research Grant for Healthcare Innovation',
    description: 'Funding opportunity for artificial intelligence research focused on healthcare applications. This grant supports innovative projects that leverage machine learning and AI technologies to improve patient outcomes, diagnostic accuracy, and treatment effectiveness.',
    organization: 'National Science Foundation',
    deadline: '2024-06-15T23:59:59Z',
    amount: '$500,000',
    eligibility: 'Universities and research institutions',
    categories: ['AI', 'Healthcare', 'Research'],
    location: 'United States',
    contact_info: 'grants@nsf.gov',
    application_url: 'https://nsf.gov/apply/ai-healthcare-2024',
    requirements: [
      'PhD in relevant field required',
      'Minimum 3 years research experience',
      'Institutional affiliation required',
      'Detailed project proposal'
    ],
    site_name: 'NSF Grants Portal',
    source_url: 'https://nsf.gov/grants/ai-healthcare-2024',
    crawl_timestamp: '2024-01-15T10:00:00Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    title: 'Small Business Innovation Research (SBIR) Phase I',
    description: 'Early-stage funding for small businesses developing innovative technologies with commercial potential. Focus areas include clean energy, biotechnology, advanced manufacturing, and cybersecurity.',
    organization: 'Department of Energy',
    deadline: '2024-05-30T17:00:00Z',
    amount: '$275,000',
    eligibility: 'Small businesses with <500 employees',
    categories: ['SBIR', 'Innovation', 'Technology'],
    location: 'United States',
    contact_info: 'sbir@energy.gov',
    application_url: 'https://energy.gov/sbir/phase1-2024',
    requirements: [
      'For-profit small business',
      'Principal investigator employed by company',
      'Technology readiness level 2-4',
      'Commercialization plan required'
    ],
    site_name: 'DOE SBIR Portal',
    source_url: 'https://energy.gov/sbir/opportunities/phase1-2024',
    crawl_timestamp: '2024-01-16T10:00:00Z',
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z'
  },
  {
    id: '3',
    title: 'Climate Change Adaptation Research Fellowship',
    description: 'Postdoctoral fellowship program supporting research on climate change adaptation strategies, resilience planning, and environmental sustainability solutions.',
    organization: 'Environmental Protection Agency',
    deadline: '2024-07-01T23:59:59Z',
    amount: '$75,000/year',
    eligibility: 'Recent PhD graduates',
    categories: ['Climate', 'Environment', 'Fellowship'],
    location: 'Washington, DC',
    contact_info: 'fellowships@epa.gov',
    application_url: 'https://epa.gov/fellowships/climate-adaptation-2024',
    requirements: [
      'PhD completed within last 3 years',
      'Research proposal in climate adaptation',
      'Two letters of recommendation',
      'Willingness to relocate to DC area'
    ],
    site_name: 'EPA Fellowships',
    source_url: 'https://epa.gov/fellowships/climate-adaptation-2024',
    crawl_timestamp: '2024-01-17T10:00:00Z',
    created_at: '2024-01-17T10:00:00Z',
    updated_at: '2024-01-17T10:00:00Z'
  }
]

export default function OpportunitiesPage() {
  const router = useRouter()
  const [opportunities] = useState<Opportunity[]>(mockOpportunities)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [sortBy, setSortBy] = useState<'deadline' | 'amount' | 'created_at'>('deadline')

  // Memoize unique categories calculation
  const categories = useMemo(() => {
    return Array.from(
      new Set(opportunities.flatMap(opp => opp.categories))
    ).sort()
  }, [opportunities])

  // Memoize expensive filtering and sorting operations
  const filteredOpportunities = useMemo(() => {
    return opportunities
      .filter(opp => {
        const matchesSearch = searchTerm === '' || 
          opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          opp.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          opp.organization.toLowerCase().includes(searchTerm.toLowerCase())
        
        const matchesCategory = selectedCategory === '' || 
          opp.categories.includes(selectedCategory)
        
        return matchesSearch && matchesCategory
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'deadline':
            if (!a.deadline && !b.deadline) return 0
            if (!a.deadline) return 1
            if (!b.deadline) return -1
            return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
          case 'amount':
            // Simple amount comparison (would need better parsing in real app)
            const aAmount = a.amount?.replace(/[^0-9]/g, '') || '0'
            const bAmount = b.amount?.replace(/[^0-9]/g, '') || '0'
            return parseInt(bAmount) - parseInt(aAmount)
          case 'created_at':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          default:
            return 0
        }
      })
  }, [opportunities, searchTerm, selectedCategory, sortBy])

  // Memoize event handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value)
  }, [])

  const handleCategoryChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value)
  }, [])

  const handleSortChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSortBy(e.target.value as 'deadline' | 'amount' | 'created_at')
  }, [])

  const handleOpportunityClick = useCallback((id: string) => {
    router.push(`/opportunities/${id}`)
  }, [router])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Opportunities</h1>
          <p className="text-muted-foreground">
            Discover grants, fellowships, and funding opportunities
          </p>
        </div>
        <div className="text-sm text-muted-foreground">
          {filteredOpportunities.length} of {opportunities.length} opportunities
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search opportunities..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full px-4 py-2 border border-input rounded-md"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={selectedCategory}
            onChange={handleCategoryChange}
            className="px-3 py-2 border border-input rounded-md"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={handleSortChange}
            className="px-3 py-2 border border-input rounded-md"
          >
            <option value="deadline">Sort by Deadline</option>
            <option value="amount">Sort by Amount</option>
            <option value="created_at">Sort by Date Added</option>
          </select>
        </div>
      </div>

      {/* Opportunities Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredOpportunities.map((opportunity) => (
          <div
            key={opportunity.id}
            className="border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleOpportunityClick(opportunity.id)}
          >
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-lg leading-tight">
                  {opportunity.title}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {opportunity.organization}
                </p>
              </div>

              <p className="text-sm text-muted-foreground line-clamp-3">
                {truncateText(opportunity.description, 150)}
              </p>

              <div className="flex flex-wrap gap-1">
                {opportunity.categories.slice(0, 3).map((category) => (
                  <span
                    key={category}
                    className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
                  >
                    {category}
                  </span>
                ))}
                {opportunity.categories.length > 3 && (
                  <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-full">
                    +{opportunity.categories.length - 3}
                  </span>
                )}
              </div>

              <div className="flex justify-between items-center text-sm">
                <div>
                  {opportunity.amount && (
                    <span className="font-medium text-green-600">
                      {opportunity.amount}
                    </span>
                  )}
                </div>
                <div>
                  {opportunity.deadline && (
                    <span className="text-muted-foreground">
                      Due: {formatDate(opportunity.deadline)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredOpportunities.length === 0 && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium mb-2">No opportunities found</h3>
            <p className="text-sm">
              {searchTerm || selectedCategory 
                ? 'Try adjusting your search criteria'
                : 'No opportunities have been crawled yet'
              }
            </p>
          </div>
        </div>
      )}
    </div>
  )
} 