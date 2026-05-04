import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Info,
  RefreshCw,
  ExternalLink,
  Activity
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

// Type definitions
interface Alert {
  title: string
  severity: string
  resource: string
  time: string
}

interface ControlInfo {
  name: string
  count: number
  critical: number
  high: number
}

interface SecurityHubData {
  severity_summary: Record<string, number>
  findings_by_control: Record<string, ControlInfo>
  recent_alerts: Alert[]
  total_active_findings: number
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
  INFORMATIONAL: '#3b82f6'
}

const SEVERITY_ICONS: Record<string, typeof AlertCircle> = {
  CRITICAL: AlertCircle,
  HIGH: AlertTriangle,
  MEDIUM: Info,
  LOW: CheckCircle,
  INFORMATIONAL: Info
}

// API Gateway endpoint
const API_URL = "https://zc06lwmk4j.execute-api.us-east-1.amazonaws.com/prod"

// Default data structure
const defaultData: SecurityHubData = {
  severity_summary: { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFORMATIONAL: 0 },
  findings_by_control: {
    "AC-2": { name: "Account Management", count: 0, critical: 0, high: 0 },
    "AU-6": { name: "Audit Review", count: 0, critical: 0, high: 0 },
    "CM-6": { name: "Configuration Settings", count: 0, critical: 0, high: 0 },
    "SI-2": { name: "Flaw Remediation", count: 0, critical: 0, high: 0 },
    "RA-5": { name: "Vulnerability Scanning", count: 0, critical: 0, high: 0 }
  },
  recent_alerts: [],
  total_active_findings: 0
}

export default function SecurityHub() {
  const [data, setData] = useState<SecurityHubData>(defaultData)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/securityhub`)
      if (!response.ok) throw new Error('Failed to fetch data')
      const result = await response.json()
      if (result.status === 'SUCCESS') {
        setData(result)
        setLastUpdated(new Date())
      } else {
        throw new Error(result.message || 'Unknown error')
      }
    } catch (err) {
      console.error('Error fetching Security Hub data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const refreshData = async () => {
    await fetchData()
  }

  // Prepare chart data
  const severityChartData = Object.entries(data.severity_summary).map(([name, value]) => ({
    name,
    value,
    color: SEVERITY_COLORS[name as keyof typeof SEVERITY_COLORS]
  }))

  const controlChartData = Object.entries(data.findings_by_control).map(([id, info]) => ({
    name: id,
    findings: info.count,
    critical: info.critical,
    high: info.high
  }))

  const totalFindings = data.total_active_findings

  return (
    <div className="min-h-screen bg-dark-bg p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-dark-text flex items-center gap-3">
              <Shield className="w-8 h-8 text-slyk-primary" />
              Security Hub
            </h1>
            <p className="text-dark-muted mt-1">
              AWS Security Hub findings mapped to NIST 800-53 controls
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-dark-muted">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
            <button
              onClick={refreshData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-slyk-primary/20 text-slyk-primary rounded-xl hover:bg-slyk-primary/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <a
              href="https://console.aws.amazon.com/securityhub"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-dark-card text-dark-text rounded-xl hover:bg-dark-border/50 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Open Security Hub
            </a>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-dark-border/50"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Total Findings</p>
                <p className="text-3xl font-bold text-dark-text mt-1">{totalFindings}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Activity className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-red-500/30"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Critical</p>
                <p className="text-3xl font-bold text-red-500 mt-1">{data.severity_summary.CRITICAL}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-orange-500/30"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">High</p>
                <p className="text-3xl font-bold text-orange-500 mt-1">{data.severity_summary.HIGH}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-500" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-yellow-500/30"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Medium</p>
                <p className="text-3xl font-bold text-yellow-500 mt-1">{data.severity_summary.MEDIUM}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                <Info className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Severity Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-dark-border/50"
          >
            <h3 className="text-lg font-semibold text-dark-text mb-4">Findings by Severity</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a1a2e',
                      border: '1px solid #2d2d44',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-4 mt-4">
              {severityChartData.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-dark-muted">
                    {item.name}: {item.value}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Findings by Control */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-dark-border/50"
          >
            <h3 className="text-lg font-semibold text-dark-text mb-4">Findings by NIST Control</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={controlChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d2d44" />
                  <XAxis type="number" stroke="#6b7280" />
                  <YAxis dataKey="name" type="category" stroke="#6b7280" width={50} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a1a2e',
                      border: '1px solid #2d2d44',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="findings" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* Control Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-dark-border/50"
        >
          <h3 className="text-lg font-semibold text-dark-text mb-4">NIST 800-53 Control Mapping</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {Object.entries(data.findings_by_control).map(([id, info]) => (
              <div
                key={id}
                className={`p-4 rounded-xl border ${
                  info.critical > 0
                    ? 'border-red-500/50 bg-red-500/10'
                    : info.high > 0
                    ? 'border-orange-500/50 bg-orange-500/10'
                    : info.count > 0
                    ? 'border-yellow-500/50 bg-yellow-500/10'
                    : 'border-green-500/50 bg-green-500/10'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-dark-text">{id}</span>
                  <span className={`text-2xl font-bold ${
                    info.critical > 0 ? 'text-red-500' :
                    info.high > 0 ? 'text-orange-500' :
                    info.count > 0 ? 'text-yellow-500' : 'text-green-500'
                  }`}>
                    {info.count}
                  </span>
                </div>
                <p className="text-sm text-dark-muted">{info.name}</p>
                {(info.critical > 0 || info.high > 0) && (
                  <div className="flex gap-2 mt-2 text-xs">
                    {info.critical > 0 && (
                      <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded">
                        {info.critical} Critical
                      </span>
                    )}
                    {info.high > 0 && (
                      <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded">
                        {info.high} High
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border border-dark-border/50"
        >
          <h3 className="text-lg font-semibold text-dark-text mb-4">Recent Findings</h3>
          <div className="space-y-3">
            {data.recent_alerts.map((alert, index) => {
              const SeverityIcon = SEVERITY_ICONS[alert.severity as keyof typeof SEVERITY_ICONS] || Info
              const severityColor = SEVERITY_COLORS[alert.severity as keyof typeof SEVERITY_COLORS] || '#6b7280'
              
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className="flex items-center gap-4 p-4 bg-dark-bg/50 rounded-xl"
                >
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${severityColor}20` }}
                  >
                    <SeverityIcon className="w-5 h-5" style={{ color: severityColor }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-dark-text font-medium">{alert.title}</p>
                    <p className="text-sm text-dark-muted">
                      {alert.resource} • {alert.time}
                    </p>
                  </div>
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: `${severityColor}20`,
                      color: severityColor
                    }}
                  >
                    {alert.severity}
                  </span>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
