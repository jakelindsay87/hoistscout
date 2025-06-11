import Link from 'next/link'

export default function Home() {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">Welcome to HoistScraper</h1>
      <p className="text-lg text-muted-foreground mb-8">
        AI-powered web scraping platform for opportunities and grants
      </p>
      <div className="space-x-4">
        <Link 
          href="/sites" 
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Manage Sites
        </Link>
        <Link 
          href="/opportunities" 
          className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
        >
          View Opportunities
        </Link>
      </div>
    </div>
  )
} 