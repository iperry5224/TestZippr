import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface ComplianceGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  animated?: boolean
}

export default function ComplianceGauge({ 
  score, 
  size = 'md', 
  showLabel = true,
  animated = true 
}: ComplianceGaugeProps) {
  const [displayScore, setDisplayScore] = useState(animated ? 0 : score)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setDisplayScore(score), 100)
      return () => clearTimeout(timer)
    }
  }, [score, animated])

  const sizes = {
    sm: { width: 120, stroke: 8, fontSize: 'text-2xl' },
    md: { width: 180, stroke: 10, fontSize: 'text-4xl' },
    lg: { width: 240, stroke: 12, fontSize: 'text-5xl' },
  }

  const { width, stroke, fontSize } = sizes[size]
  const radius = (width - stroke) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (displayScore / 100) * circumference

  const getColor = (score: number) => {
    if (score >= 80) return { color: '#10B981', glow: 'rgba(16, 185, 129, 0.4)' }
    if (score >= 60) return { color: '#F59E0B', glow: 'rgba(245, 158, 11, 0.4)' }
    return { color: '#EF4444', glow: 'rgba(239, 68, 68, 0.4)' }
  }

  const { color, glow } = getColor(displayScore)

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={width} height={width} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-dark-border/30"
        />
        {/* Progress circle */}
        <motion.circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 10px ${glow})` }}
        />
      </svg>
      
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className={`${fontSize} font-bold`}
          style={{ color }}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          {Math.round(displayScore)}%
        </motion.span>
        {showLabel && (
          <span className="text-sm text-dark-muted mt-1">Compliance</span>
        )}
      </div>
    </div>
  )
}
