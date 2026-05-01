import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, CheckCircle, XCircle, Bell, X } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

interface Alert {
  id: string
  type: 'critical' | 'warning' | 'info' | 'success'
  title: string
  message: string
  timestamp: string
  controlId?: string
  acknowledged?: boolean
}

interface AlertsFeedProps {
  alerts: Alert[]
  onAcknowledge?: (id: string) => void
  onDismiss?: (id: string) => void
  maxItems?: number
}

const alertConfig = {
  critical: {
    icon: XCircle,
    color: 'text-slyk-danger',
    bg: 'bg-slyk-danger/10',
    border: 'border-slyk-danger/30',
    pulse: true
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-slyk-warning',
    bg: 'bg-slyk-warning/10',
    border: 'border-slyk-warning/30',
    pulse: false
  },
  info: {
    icon: Bell,
    color: 'text-slyk-accent',
    bg: 'bg-slyk-accent/10',
    border: 'border-slyk-accent/30',
    pulse: false
  },
  success: {
    icon: CheckCircle,
    color: 'text-slyk-success',
    bg: 'bg-slyk-success/10',
    border: 'border-slyk-success/30',
    pulse: false
  }
}

export default function AlertsFeed({ 
  alerts, 
  onAcknowledge, 
  onDismiss,
  maxItems = 5 
}: AlertsFeedProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const displayAlerts = alerts.slice(0, maxItems)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-dark-text flex items-center gap-2">
          <Bell className="w-5 h-5 text-slyk-primary" />
          Live Alerts
          {alerts.filter(a => !a.acknowledged).length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-slyk-danger/20 text-slyk-danger">
              {alerts.filter(a => !a.acknowledged).length} new
            </span>
          )}
        </h3>
      </div>

      <AnimatePresence mode="popLayout">
        {displayAlerts.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-8 text-dark-muted"
          >
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-slyk-success/50" />
            <p>No active alerts</p>
            <p className="text-sm">All systems operating normally</p>
          </motion.div>
        ) : (
          displayAlerts.map((alert, index) => {
            const config = alertConfig[alert.type]
            const Icon = config.icon
            const isExpanded = expandedId === alert.id

            return (
              <motion.div
                key={alert.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                className={clsx(
                  'p-4 rounded-xl border transition-all cursor-pointer',
                  config.bg,
                  config.border,
                  alert.acknowledged && 'opacity-60'
                )}
                onClick={() => setExpandedId(isExpanded ? null : alert.id)}
              >
                <div className="flex items-start gap-3">
                  <div className={clsx(
                    'p-2 rounded-lg',
                    config.bg,
                    config.pulse && 'animate-pulse'
                  )}>
                    <Icon className={clsx('w-5 h-5', config.color)} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-dark-text truncate">
                        {alert.title}
                      </h4>
                      {alert.controlId && (
                        <span className="text-xs font-mono text-slyk-primary">
                          {alert.controlId}
                        </span>
                      )}
                    </div>
                    
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.p
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="text-sm text-dark-muted mt-2"
                        >
                          {alert.message}
                        </motion.p>
                      )}
                    </AnimatePresence>
                    
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs text-dark-muted">
                        {alert.timestamp}
                      </span>
                      
                      {!alert.acknowledged && onAcknowledge && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onAcknowledge(alert.id)
                          }}
                          className="text-xs text-slyk-primary hover:underline"
                        >
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>

                  {onDismiss && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onDismiss(alert.id)
                      }}
                      className="p-1 rounded hover:bg-dark-border/30 text-dark-muted hover:text-dark-text"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </motion.div>
            )
          })
        )}
      </AnimatePresence>

      {alerts.length > maxItems && (
        <button className="w-full py-2 text-sm text-slyk-primary hover:underline">
          View all {alerts.length} alerts
        </button>
      )}
    </div>
  )
}
