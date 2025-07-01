"use client"

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Search, Filter, Download, Pause, Play, Trash2 } from 'lucide-react'
import { format } from 'date-fns'

interface LogEvent {
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL'
  service: 'scraper' | 'api' | 'worker' | 'database' | 'auth'
  correlationId?: string
  message: string
  metadata?: Record<string, any>
  performance?: {
    memoryUsage: number
    cpuUsage: number
    networkLatency: number
  }
}

interface LogViewerProps {
  websocketUrl?: string
}

export function LogViewer({ websocketUrl = 'ws://localhost:8000/ws/logs' }: LogViewerProps) {
  const [logs, setLogs] = useState<LogEvent[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEvent[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [serviceFilter, setServiceFilter] = useState<string>('all')
  const [autoScroll, setAutoScroll] = useState(true)
  
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const maxLogs = 1000

  // WebSocket connection
  useEffect(() => {
    if (!isPaused) {
      wsRef.current = new WebSocket(websocketUrl)
      
      wsRef.current.onmessage = (event) => {
        try {
          const logEvent: LogEvent = JSON.parse(event.data)
          setLogs(prev => {
            const newLogs = [logEvent, ...prev]
            return newLogs.slice(0, maxLogs)
          })
        } catch (error) {
          console.error('Failed to parse log event:', error)
        }
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [websocketUrl, isPaused])

  // Filter logs
  useEffect(() => {
    let filtered = logs

    // Level filter
    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter)
    }

    // Service filter
    if (serviceFilter !== 'all') {
      filtered = filtered.filter(log => log.service === serviceFilter)
    }

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(log => {
        const searchLower = searchTerm.toLowerCase()
        return (
          log.message.toLowerCase().includes(searchLower) ||
          log.correlationId?.toLowerCase().includes(searchLower) ||
          JSON.stringify(log.metadata).toLowerCase().includes(searchLower)
        )
      })
    }

    setFilteredLogs(filtered)
  }, [logs, levelFilter, serviceFilter, searchTerm])

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = 0
    }
  }, [filteredLogs, autoScroll])

  const getLevelColor = (level: LogEvent['level']) => {
    switch (level) {
      case 'DEBUG': return 'bg-gray-500'
      case 'INFO': return 'bg-blue-500'
      case 'WARN': return 'bg-yellow-500'
      case 'ERROR': return 'bg-red-500'
      case 'CRITICAL': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  const getServiceColor = (service: LogEvent['service']) => {
    switch (service) {
      case 'scraper': return 'bg-green-500'
      case 'api': return 'bg-blue-500'
      case 'worker': return 'bg-orange-500'
      case 'database': return 'bg-purple-500'
      case 'auth': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const exportLogs = useCallback(() => {
    const logsText = filteredLogs.map(log => 
      `[${log.timestamp}] [${log.level}] [${log.service}] ${log.message} ${JSON.stringify(log.metadata || {})}`
    ).join('\n')
    
    const blob = new Blob([logsText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${format(new Date(), 'yyyy-MM-dd_HH-mm-ss')}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }, [filteredLogs])

  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Live System Logs</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              {isPaused ? 'Paused' : 'Live'}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {filteredLogs.length} / {logs.length} logs
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex flex-wrap gap-2">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
          
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Levels</SelectItem>
              <SelectItem value="DEBUG">Debug</SelectItem>
              <SelectItem value="INFO">Info</SelectItem>
              <SelectItem value="WARN">Warning</SelectItem>
              <SelectItem value="ERROR">Error</SelectItem>
              <SelectItem value="CRITICAL">Critical</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={serviceFilter} onValueChange={setServiceFilter}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Service" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Services</SelectItem>
              <SelectItem value="scraper">Scraper</SelectItem>
              <SelectItem value="api">API</SelectItem>
              <SelectItem value="worker">Worker</SelectItem>
              <SelectItem value="database">Database</SelectItem>
              <SelectItem value="auth">Auth</SelectItem>
            </SelectContent>
          </Select>
          
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsPaused(!isPaused)}
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={exportLogs}
              title="Export logs"
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={clearLogs}
              title="Clear logs"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Log entries */}
        <ScrollArea className="h-[600px] w-full rounded-md border" ref={scrollAreaRef}>
          <div className="p-4 space-y-2">
            {filteredLogs.map((log, index) => (
              <div
                key={`${log.timestamp}-${index}`}
                className="flex flex-col space-y-1 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge className={getLevelColor(log.level)} variant="secondary">
                      {log.level}
                    </Badge>
                    <Badge className={getServiceColor(log.service)} variant="secondary">
                      {log.service}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
                    </span>
                    {log.correlationId && (
                      <span className="text-xs text-muted-foreground font-mono">
                        {log.correlationId.slice(0, 8)}
                      </span>
                    )}
                  </div>
                  
                  {log.performance && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>Mem: {log.performance.memoryUsage.toFixed(1)}MB</span>
                      <span>CPU: {log.performance.cpuUsage.toFixed(1)}%</span>
                    </div>
                  )}
                </div>
                
                <div className="text-sm">{log.message}</div>
                
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="text-xs text-muted-foreground font-mono">
                    {Object.entries(log.metadata).map(([key, value]) => (
                      <span key={key} className="mr-3">
                        {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}