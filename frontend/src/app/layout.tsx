import type { Metadata } from 'next'
import Link from 'next/link'
import { Inter } from 'next/font/google'
import { ErrorBoundaryClass } from '@/components/ErrorBoundary'
import { ToastContainer } from '@/components/ui/toast'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HoistScraper',
  description: 'AI-powered web scraping platform for opportunities and grants',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <nav className="border-b">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-primary">HoistScraper</h1>
                <div className="flex space-x-4">
                  <Link href="/sites" className="text-foreground hover:text-primary">Sites</Link>
                  <Link href="/jobs" className="text-foreground hover:text-primary">Jobs</Link>
                  <Link href="/results" className="text-foreground hover:text-primary">Results</Link>
                </div>
              </div>
            </div>
          </nav>
          <main className="container mx-auto px-4 py-8">
            <ErrorBoundaryClass>
              {children}
            </ErrorBoundaryClass>
          </main>
        </div>
        <ToastContainer />
      </body>
    </html>
  )
} 