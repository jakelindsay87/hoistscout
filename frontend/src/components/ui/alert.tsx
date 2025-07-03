import { ReactNode } from 'react'

interface AlertProps {
  children: ReactNode
  variant?: 'default' | 'destructive'
  className?: string
}

export function Alert({ children, variant = 'default', className = '' }: AlertProps) {
  const variantStyles = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800'
  }

  return (
    <div className={`border rounded-md p-4 ${variantStyles[variant]} ${className}`} role="alert">
      {children}
    </div>
  )
}

export function AlertDescription({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  )
}