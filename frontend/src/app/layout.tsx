import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ErrorBoundaryClass } from '@/components/ErrorBoundary'
import { ToastContainer } from '@/components/ui/toast'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import './globals.css'
// Initialize API configuration and logging
import '@/lib/init-api-config'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HoistScraper - Australian Grant Discovery Platform',
  description: 'AI-powered platform for discovering Australian grants and funding opportunities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-slate-50 antialiased`}>
        <div className="flex h-full">
          {/* Sidebar */}
          <Sidebar />
          
          {/* Main Content */}
          <div className="flex-1 flex flex-col ml-64">
            {/* Header */}
            <Header />
            
            {/* Main Content Area */}
            <main className="flex-1 overflow-auto">
              <div className="px-6 py-6">
                <ErrorBoundaryClass>
                  {children}
                </ErrorBoundaryClass>
              </div>
            </main>
          </div>
        </div>
        <ToastContainer />
      </body>
    </html>
  )
} 