import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ErrorBoundaryClass } from '@/components/ErrorBoundary'
import { ToastContainer } from '@/components/ui/toast'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { AuthProvider } from '@/contexts/AuthContext'
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
        <AuthProvider>
          {children}
        </AuthProvider>
        <ToastContainer />
      </body>
    </html>
  )
} 