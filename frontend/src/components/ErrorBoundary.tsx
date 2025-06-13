'use client'

import React from 'react'

interface ErrorBoundaryProps {
  error?: Error
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>
}

interface ErrorFallbackProps {
  error: Error
  retry: () => void
}

const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, retry }) => (
  <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
    <div className="max-w-md">
      <div className="text-6xl mb-4">⚠️</div>
      <h2 className="text-2xl font-semibold text-red-600 mb-3">
        Something went wrong
      </h2>
      <p className="text-gray-600 mb-6 text-sm leading-relaxed">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <div className="space-y-3">
        <button 
          onClick={retry}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
        >
          Try Again
        </button>
        <button 
          onClick={() => window.location.reload()}
          className="w-full px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
        >
          Reload Page
        </button>
      </div>
    </div>
  </div>
)

export function ErrorBoundary({ 
  error, 
  children, 
  fallback: Fallback = DefaultErrorFallback 
}: ErrorBoundaryProps) {
  const retry = () => {
    window.location.reload()
  }

  if (error) {
    return <Fallback error={error} retry={retry} />
  }

  return <>{children}</>
}

// Higher-order component for class-based error boundary
export class ErrorBoundaryClass extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error: Error; retry: () => void }> },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      const Fallback = this.props.fallback || DefaultErrorFallback
      return (
        <Fallback 
          error={this.state.error} 
          retry={() => this.setState({ hasError: false, error: undefined })} 
        />
      )
    }

    return this.props.children
  }
}