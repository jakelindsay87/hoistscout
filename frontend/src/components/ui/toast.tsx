'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

export interface Toast {
  id: string
  title: string
  description?: string
  type?: 'default' | 'success' | 'error' | 'warning'
  duration?: number
}

interface ToastProps extends Toast {
  onDismiss: (id: string) => void
}

const ToastItem: React.FC<ToastProps> = ({ 
  id, 
  title, 
  description, 
  type = 'default', 
  duration = 5000,
  onDismiss 
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onDismiss(id), duration)
      return () => clearTimeout(timer)
    }
  }, [id, duration, onDismiss])

  const typeStyles = {
    default: 'bg-white border-gray-200',
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200'
  }

  const iconMap = {
    default: '💬',
    success: '✅',
    error: '❌',
    warning: '⚠️'
  }

  return (
    <div className={cn(
      'flex items-start gap-3 w-full max-w-sm p-4 rounded-lg border shadow-lg transition-all',
      typeStyles[type]
    )}>
      <span className="text-xl">{iconMap[type]}</span>
      <div className="flex-1">
        <h3 className="font-semibold text-sm">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="ml-2 text-gray-400 hover:text-gray-600"
      >
        ×
      </button>
    </div>
  )
}

// Toast container component
export const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const handleToast = (event: CustomEvent<Toast>) => {
      const toast = { ...event.detail, id: event.detail.id || Date.now().toString() }
      setToasts(prev => [...prev, toast])
    }

    window.addEventListener('toast' as any, handleToast)
    return () => window.removeEventListener('toast' as any, handleToast)
  }, [])

  const dismissToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          {...toast}
          onDismiss={dismissToast}
        />
      ))}
    </div>
  )
}

// Helper function to show toast
export const toast = (options: Omit<Toast, 'id'>) => {
  const event = new CustomEvent('toast', {
    detail: { ...options, id: Date.now().toString() }
  })
  window.dispatchEvent(event)
}