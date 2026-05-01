import { motion } from 'framer-motion'
import { CheckCircle, XCircle, AlertTriangle, ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

interface ControlCardProps {
  controlId: string
  name: string
  description: string
  status: 'PASS' | 'FAIL' | 'WARNING' | 'PENDING'
  findings?: number
  lastChecked?: string
  onClick?: () => void
}

const statusConfig = {
  PASS: {
    icon: CheckCircle,
    color: 'text-slyk-success',
    bg: 'bg-slyk-success/10',
    border: 'border-slyk-success/30',
    glow: 'hover:shadow-glow-success',
    label: 'Compliant'
  },
  FAIL: {
    icon: XCircle,
    color: 'text-slyk-danger',
    bg: 'bg-slyk-danger/10',
    border: 'border-slyk-danger/30',
    glow: 'hover:shadow-glow-danger',
    label: 'Non-Compliant'
  },
  WARNING: {
    icon: AlertTriangle,
    color: 'text-slyk-warning',
    bg: 'bg-slyk-warning/10',
    border: 'border-slyk-warning/30',
    glow: 'hover:shadow-[0_0_20px_rgba(245,158,11,0.3)]',
    label: 'Needs Attention'
  },
  PENDING: {
    icon: AlertTriangle,
    color: 'text-dark-muted',
    bg: 'bg-dark-border/10',
    border: 'border-dark-border/30',
    glow: '',
    label: 'Not Assessed'
  }
}

export default function ControlCard({
  controlId,
  name,
  description,
  status,
  findings = 0,
  lastChecked,
  onClick
}: ControlCardProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Link
        to={`/controls/${controlId}`}
        onClick={onClick}
        className={clsx(
          'block glass-card p-5 transition-all duration-300',
          config.glow
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-12 h-12 rounded-xl flex items-center justify-center',
              config.bg,
              'border',
              config.border
            )}>
              <Icon className={clsx('w-6 h-6', config.color)} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono text-slyk-primary">{controlId}</span>
                <span className={clsx(
                  'px-2 py-0.5 rounded-full text-xs font-medium',
                  config.bg,
                  config.color
                )}>
                  {config.label}
                </span>
              </div>
              <h3 className="font-semibold text-dark-text mt-1">{name}</h3>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-dark-muted" />
        </div>

        <p className="text-sm text-dark-muted mt-3 line-clamp-2">{description}</p>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-dark-border/30">
          {findings > 0 && (
            <span className="text-sm">
              <span className={config.color}>{findings}</span>
              <span className="text-dark-muted"> findings</span>
            </span>
          )}
          {lastChecked && (
            <span className="text-xs text-dark-muted">
              Last checked: {lastChecked}
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  )
}
