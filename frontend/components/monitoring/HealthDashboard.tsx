"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { 
  Activity, Database, Server, HardDrive, Cpu, 
  CheckCircle, XCircle, AlertCircle, RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface HealthCheck {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  details: Record<string, any>
  response_time_ms: number
  timestamp: string
}

interface HealthData {
  timestamp: string
  overall_status: 'healthy' | 'degraded' | 'unhealthy'
  health_score: number
  checks: Record<string, HealthCheck>
  summary: {
    total_checks: number
    healthy: number
    degraded: number
    unhealthy: number
    critical_issues: string[]
  }
}

export function HealthDashboard() {
  const [healthData, setHealthData] = useState<HealthData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchHealthData = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/health/detailed')
      const data = await response.json()
      setHealthData(data)
    } catch (error) {
      console.error('Failed to fetch health data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchHealthData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchHealthData, 30000) // Refresh every 30 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'unhealthy':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getServiceIcon = (name: string) => {
    switch (name) {
      case 'database':
        return <Database className="h-4 w-4" />
      case 'redis':
        return <Server className="h-4 w-4" />
      case 'disk_space':
        return <HardDrive className="h-4 w-4" />
      case 'memory_usage':
        return <Cpu className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  if (isLoading && !healthData) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!healthData) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>Failed to load health data</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      {/* Overall Health Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>System Health</CardTitle>
              {getStatusIcon(healthData.overall_status)}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchHealthData}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold">Health Score</span>
              <div className="flex items-center gap-2">
                <Progress value={healthData.health_score} className="w-32" />
                <span className="text-2xl font-bold">{healthData.health_score.toFixed(0)}%</span>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">
                  {healthData.summary.healthy}
                </div>
                <div className="text-sm text-muted-foreground">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-500">
                  {healthData.summary.degraded}
                </div>
                <div className="text-sm text-muted-foreground">Degraded</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-500">
                  {healthData.summary.unhealthy}
                </div>
                <div className="text-sm text-muted-foreground">Unhealthy</div>
              </div>
            </div>
            
            {healthData.summary.critical_issues.length > 0 && (
              <Alert variant="destructive">
                <AlertTitle>Critical Issues</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside">
                    {healthData.summary.critical_issues.map((issue, index) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Individual Service Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(healthData.checks).map(([name, check]) => (
          <Card key={name} className={check.status === 'unhealthy' ? 'border-red-500' : ''}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getServiceIcon(name)}
                  <CardTitle className="text-base">
                    {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </CardTitle>
                </div>
                <Badge className={getStatusColor(check.status)} variant="secondary">
                  {check.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Response Time</span>
                  <span className="font-mono">{check.response_time_ms.toFixed(1)}ms</span>
                </div>
                
                {/* Service-specific details */}
                {name === 'database' && check.details.connection && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Active Connections</span>
                      <span>{check.details.active_connections}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Opportunities</span>
                      <span>{check.details.opportunities_count || 0}</span>
                    </div>
                  </>
                )}
                
                {name === 'redis' && check.details.connection && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Memory Usage</span>
                      <span>{check.details.memory_usage_mb?.toFixed(1) || 0}MB</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Connected Clients</span>
                      <span>{check.details.connected_clients || 0}</span>
                    </div>
                  </>
                )}
                
                {name === 'disk_space' && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Used / Total</span>
                      <span>
                        {check.details.used_gb?.toFixed(1) || 0}GB / 
                        {check.details.total_gb?.toFixed(1) || 0}GB
                      </span>
                    </div>
                    <Progress 
                      value={check.details.percent_used || 0} 
                      className="h-2"
                    />
                  </>
                )}
                
                {name === 'memory_usage' && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Used / Total</span>
                      <span>
                        {check.details.used_gb?.toFixed(1) || 0}GB / 
                        {check.details.total_gb?.toFixed(1) || 0}GB
                      </span>
                    </div>
                    <Progress 
                      value={check.details.percent_used || 0} 
                      className="h-2"
                    />
                  </>
                )}
                
                {name === 'background_jobs' && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Worker Processes</span>
                      <span>{check.details.worker_processes || 0}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pending Jobs</span>
                      <span>{check.details.pending_jobs || 0}</span>
                    </div>
                  </>
                )}
                
                {check.details.error && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertDescription className="text-xs">
                      {check.details.error}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}