import { http, HttpResponse } from 'msw'

export const handlers = [
  // Websites endpoints
  http.get('http://localhost:8000/api/websites', () => {
    return HttpResponse.json([
      {
        id: 1,
        url: 'https://example.com',
        name: 'Example Site',
        description: 'Test site',
        created_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        url: 'https://test.com',
        name: 'Test Site',
        created_at: '2024-01-02T00:00:00Z'
      }
    ])
  }),

  http.post('http://localhost:8000/api/websites', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      id: 3,
      url: body.url,
      name: body.name,
      description: body.description,
      created_at: new Date().toISOString()
    })
  }),

  // Jobs endpoints
  http.get('http://localhost:8000/api/jobs', ({ request }) => {
    const url = new URL(request.url)
    const websiteId = url.searchParams.get('website_id')
    
    const jobs = [
      {
        id: 'job-1',
        website_id: 1,
        status: 'completed',
        started_at: '2024-01-01T10:00:00Z',
        completed_at: '2024-01-01T10:05:00Z',
        result_path: '/data/job-1.json'
      },
      {
        id: 'job-2',
        website_id: 2,
        status: 'running',
        started_at: '2024-01-01T10:10:00Z'
      }
    ]

    if (websiteId) {
      return HttpResponse.json(jobs.filter(job => job.website_id === parseInt(websiteId)))
    }
    
    return HttpResponse.json(jobs)
  }),

  http.post('http://localhost:8000/api/scrape/:siteId', ({ params }) => {
    return HttpResponse.json({
      id: 'job-3',
      website_id: parseInt(params.siteId as string),
      status: 'pending'
    })
  }),

  // Results endpoints
  http.get('http://localhost:8000/api/results/:jobId', ({ params }) => {
    return HttpResponse.json({
      jobId: params.jobId,
      websiteId: 1,
      url: 'https://example.com',
      scrapedAt: '2024-01-01T10:05:00Z',
      data: {
        title: 'Example Page',
        content: 'Example content',
        links: ['https://example.com/page1', 'https://example.com/page2']
      }
    })
  })
]