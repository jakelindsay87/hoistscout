'use client'

import React from 'react'
import { Opportunity } from '@/types'
import { formatDate, formatDateTime } from '@/lib/utils'

// Mock data - in real app this would come from API based on params.id
const mockOpportunity: Opportunity = {
  id: '1',
  title: 'AI Research Grant for Healthcare Innovation',
  description: 'Funding opportunity for artificial intelligence research focused on healthcare applications. This grant supports innovative projects that leverage machine learning and AI technologies to improve patient outcomes, diagnostic accuracy, and treatment effectiveness. The program aims to accelerate the development of AI-driven solutions that can be translated into clinical practice, with particular emphasis on addressing health disparities and improving access to quality healthcare. Successful applicants will have access to state-of-the-art computing resources, mentorship from leading AI researchers, and opportunities for collaboration with healthcare institutions.',
  organization: 'National Science Foundation',
  deadline: '2024-06-15T23:59:59Z',
  amount: '$500,000',
  eligibility: 'Universities and research institutions with established AI research programs. Principal investigators must hold a PhD in computer science, biomedical engineering, or related field with demonstrated expertise in artificial intelligence and healthcare applications.',
  categories: ['AI', 'Healthcare', 'Research', 'Machine Learning', 'Innovation'],
  location: 'United States',
  contact_info: 'grants@nsf.gov',
  application_url: 'https://nsf.gov/apply/ai-healthcare-2024',
  requirements: [
    'PhD in relevant field (Computer Science, Biomedical Engineering, or related) required',
    'Minimum 3 years of research experience in AI/ML applications',
    'Institutional affiliation with accredited university or research institution required',
    'Detailed project proposal with clear healthcare impact statement',
    'Budget justification and timeline for 24-month project period',
    'Letters of support from healthcare partners or clinical collaborators',
    'Data management and sharing plan compliant with NIH guidelines',
    'Human subjects research approval if applicable'
  ],
  site_name: 'NSF Grants Portal',
  source_url: 'https://nsf.gov/grants/ai-healthcare-2024',
  crawl_timestamp: '2024-01-15T10:00:00Z',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z'
}

interface OpportunityDetailPageProps {
  params: {
    id: string
  }
}

export default function OpportunityDetailPage({ params }: OpportunityDetailPageProps) {
  // In a real app, you would fetch the opportunity based on params.id
  const opportunity = mockOpportunity

  if (!opportunity) {
    return (
      <div className="text-center py-12">
        <div className="text-muted-foreground">
          <div className="text-4xl mb-4">❌</div>
          <h3 className="text-lg font-medium mb-2">Opportunity not found</h3>
          <p className="text-sm">The requested opportunity could not be found.</p>
          <a 
            href="/opportunities" 
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 mt-4"
          >
            Back to Opportunities
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <a href="/opportunities" className="hover:text-primary">Opportunities</a>
          <span>→</span>
          <span>{opportunity.title}</span>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold leading-tight">{opportunity.title}</h1>
          <p className="text-xl text-muted-foreground">{opportunity.organization}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {opportunity.categories.map((category) => (
            <span
              key={category}
              className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
            >
              {category}
            </span>
          ))}
        </div>
      </div>

      {/* Key Information Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-sm text-muted-foreground mb-2">Funding Amount</h3>
          <p className="text-2xl font-bold text-green-600">{opportunity.amount}</p>
        </div>
        
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-sm text-muted-foreground mb-2">Application Deadline</h3>
          <p className="text-2xl font-bold">
            {opportunity.deadline ? formatDate(opportunity.deadline) : 'Not specified'}
          </p>
          {opportunity.deadline && (
            <p className="text-sm text-muted-foreground mt-1">
              {formatDateTime(opportunity.deadline)}
            </p>
          )}
        </div>
        
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-sm text-muted-foreground mb-2">Location</h3>
          <p className="text-lg font-medium">{opportunity.location || 'Not specified'}</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <section>
            <h2 className="text-xl font-semibold mb-3">Description</h2>
            <div className="prose prose-sm max-w-none">
              <p className="text-muted-foreground leading-relaxed">
                {opportunity.description}
              </p>
            </div>
          </section>

          {/* Eligibility */}
          {opportunity.eligibility && (
            <section>
              <h2 className="text-xl font-semibold mb-3">Eligibility</h2>
              <p className="text-muted-foreground leading-relaxed">
                {opportunity.eligibility}
              </p>
            </section>
          )}

          {/* Requirements */}
          <section>
            <h2 className="text-xl font-semibold mb-3">Requirements</h2>
            <ul className="space-y-2">
              {opportunity.requirements.map((requirement, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span className="text-muted-foreground">{requirement}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Apply Button */}
          {opportunity.application_url && (
            <div className="border rounded-lg p-4">
              <a
                href={opportunity.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full inline-flex items-center justify-center rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Apply Now →
              </a>
            </div>
          )}

          {/* Contact Information */}
          {opportunity.contact_info && (
            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">Contact</h3>
              <p className="text-sm text-muted-foreground">{opportunity.contact_info}</p>
            </div>
          )}

          {/* Source Information */}
          <div className="border rounded-lg p-4">
            <h3 className="font-medium mb-2">Source</h3>
            <p className="text-sm text-muted-foreground mb-2">{opportunity.site_name}</p>
            <a
              href={opportunity.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              View Original →
            </a>
          </div>

          {/* Metadata */}
          <div className="border rounded-lg p-4">
            <h3 className="font-medium mb-2">Information</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div>
                <span className="font-medium">Added:</span> {formatDate(opportunity.created_at)}
              </div>
              <div>
                <span className="font-medium">Updated:</span> {formatDate(opportunity.updated_at)}
              </div>
              {opportunity.crawl_timestamp && (
                <div>
                  <span className="font-medium">Last Crawled:</span> {formatDate(opportunity.crawl_timestamp)}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Back Button */}
      <div className="pt-8">
        <a
          href="/opportunities"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary"
        >
          ← Back to all opportunities
        </a>
      </div>
    </div>
  )
} 