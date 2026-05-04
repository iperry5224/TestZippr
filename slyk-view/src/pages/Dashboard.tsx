import { motion } from 'framer-motion'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  RefreshCw
} from 'lucide-react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import ComplianceGauge from '../components/ComplianceGauge'
import ControlCard from '../components/ControlCard'
import AlertsFeed from '../components/AlertsFeed'
import { useState, useEffect } from 'react'

// API Gateway endpoint
const API_URL = "https://zc06lwmk4j.execute-api.us-east-1.amazonaws.com/prod"

// Types
interface ControlData {
  controlId: string
  name: string
  description: string
  status: 'PASS' | 'WARNING' | 'FAIL'
  findings: number
  lastChecked: string
}

interface Alert {
  id: string
  type: 'critical' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  controlId: string
}

// Control descriptions
const CONTROL_DESCRIPTIONS: Record<string, string> = {
  'AC-2': 'Automated detection of unauthorized account creation and MFA enforcement',
  'AU-6': 'Real-time analysis of audit logs for anomalies and security events',
  'CM-6': 'Automated verification of system configuration against baselines',
  'SI-2': 'Automated remediation runbooks and patching logic',
  'RA-5': 'Security scan coverage analysis relative to total inventory'
}

export default function Dashboard() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [complianceScore, setComplianceScore] = useState(0)
  const [controlsData, setControlsData] = useState<ControlData[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [statusDistribution, setStatusDistribution] = useState([
    { name: 'Pass', value: 0, color: '#10B981' },
    { name: 'Warning', value: 0, color: '#F59E0B' },
    { name: 'Fail', value: 0, color: '#EF4444' },
  ])
  const [complianceHistory, setComplianceHistory] = useState([
    { date: 'Mon', score: 70 },
    { date: 'Tue', score: 72 },
    { date: 'Wed', score: 71 },
    { date: 'Thu', score: 74 },
    { date: 'Fri', score: 73 },
    { date: 'Sat', score: 76 },
    { date: 'Sun', score: 78 },
  ])

  const fetchData = async () => {
    try {
      const response = await fetch(`${API_URL}/securityhub`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      
      if (data.status === 'SUCCESS') {
        // Calculate compliance score based on findings
        const totalFindings = data.total_active_findings || 0
        const score = Math.max(0, Math.min(100, 100 - (totalFindings * 2)))
        setComplianceScore(score)
        
        // Update compliance history with new score
        const today = new Date().toLocaleDateString('en-US', { weekday: 'short' })
        setComplianceHistory(prev => {
          const updated = [...prev.slice(1), { date: today, score }]
          return updated
        })
        
        // Transform findings_by_control to controlsData
        const controls: ControlData[] = Object.entries(data.findings_by_control || {}).map(([id, info]: [string, any]) => {
          let status: 'PASS' | 'WARNING' | 'FAIL' = 'PASS'
          if (info.critical > 0) status = 'FAIL'
          else if (info.high > 0 || info.count > 3) status = 'WARNING'
          else if (info.count > 0) status = 'WARNING'
          
          return {
            controlId: id,
            name: info.name,
            description: CONTROL_DESCRIPTIONS[id] || info.name,
            status,
            findings: info.count,
            lastChecked: 'Just now'
          }
        })
        setControlsData(controls)
        
        // Calculate status distribution
        const pass = controls.filter(c => c.status === 'PASS').length
        const warning = controls.filter(c => c.status === 'WARNING').length
        const fail = controls.filter(c => c.status === 'FAIL').length
        setStatusDistribution([
          { name: 'Pass', value: pass, color: '#10B981' },
          { name: 'Warning', value: warning, color: '#F59E0B' },
          { name: 'Fail', value: fail, color: '#EF4444' },
        ])
        
        // Transform recent_alerts to alerts
        const newAlerts: Alert[] = (data.recent_alerts || []).map((alert: any, index: number) => ({
          id: String(index + 1),
          type: alert.severity === 'CRITICAL' ? 'critical' : alert.severity === 'HIGH' ? 'warning' : 'info',
          title: alert.title?.substring(0, 50) || 'Security Finding',
          message: `Resource: ${alert.resource || 'Unknown'}`,
          timestamp: alert.time || 'Recently',
          controlId: 'CM-6'
        }))
        setAlerts(newAlerts)
        
        setLastUpdated(new Date())
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchData()
    setIsRefreshing(false)
  }

  const previousScore = complianceHistory.length > 1 ? complianceHistory[complianceHistory.length - 2].score : complianceScore

  const getTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)
    if (seconds < 60) return 'Just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-slyk-primary animate-spin mx-auto mb-4" />
          <p className="text-dark-muted">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold gradient-text"
          >
            nesdis-ncis-ospocsta-5006
          </motion.h1>
          <p className="text-dark-muted mt-1">
            Account ID: 656443597515 • NIST 800-53 Compliance
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-dark-muted">
            <Clock className="w-4 h-4" />
            Last updated: {getTimeAgo(lastUpdated)}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary/20 text-slyk-primary hover:bg-slyk-primary/30 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total Controls</p>
              <p className="text-3xl font-bold text-dark-text mt-1">{controlsData.length}</p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-slyk-primary/20 flex items-center justify-center">
              <Shield className="w-6 h-6 text-slyk-primary" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Passing</p>
              <p className="text-3xl font-bold text-slyk-success mt-1">
                {statusDistribution.find(s => s.name === 'Pass')?.value || 0}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-slyk-success/20 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-slyk-success" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Warnings</p>
              <p className="text-3xl font-bold text-slyk-warning mt-1">
                {statusDistribution.find(s => s.name === 'Warning')?.value || 0}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-slyk-warning/20 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-slyk-warning" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Failing</p>
              <p className="text-3xl font-bold text-slyk-danger mt-1">
                {statusDistribution.find(s => s.name === 'Fail')?.value || 0}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-slyk-danger/20 flex items-center justify-center">
              <XCircle className="w-6 h-6 text-slyk-danger" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance Score & Trend */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <h2 className="text-lg font-semibold text-dark-text mb-4">Compliance Score</h2>
          
          <div className="flex flex-col items-center">
            <ComplianceGauge score={complianceScore} size="lg" />
            
            <div className="flex items-center gap-2 mt-4">
              {complianceScore >= previousScore ? (
                <>
                  <TrendingUp className="w-5 h-5 text-slyk-success" />
                  <span className="text-slyk-success">
                    {complianceScore > previousScore ? `+${complianceScore - previousScore}%` : 'No change'} from last check
                  </span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-5 h-5 text-slyk-danger" />
                  <span className="text-slyk-danger">
                    {complianceScore - previousScore}% from last check
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Mini distribution chart */}
          <div className="mt-6">
            <div className="flex justify-center">
              <PieChart width={150} height={100}>
                <Pie
                  data={statusDistribution}
                  cx={75}
                  cy={50}
                  innerRadius={30}
                  outerRadius={45}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </div>
            <div className="flex justify-center gap-4 mt-2">
              {statusDistribution.map((item) => (
                <div key={item.name} className="flex items-center gap-1 text-xs">
                  <div 
                    className="w-2 h-2 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-dark-muted">{item.name}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Trend Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6 lg:col-span-2"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-dark-text">Compliance Trend</h2>
            <div className="flex items-center gap-2 text-sm text-dark-muted">
              <Activity className="w-4 h-4" />
              Last 7 days
            </div>
          </div>
          
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={complianceHistory}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="date" 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94A3B8', fontSize: 12 }}
              />
              <YAxis 
                domain={[60, 100]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94A3B8', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#E2E8F0' }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#6366F1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorScore)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Controls & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Grid */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-dark-text">Security Controls</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {controlsData.map((control) => (
              <ControlCard key={control.controlId} {...control} />
            ))}
          </div>
        </div>

        {/* Alerts Feed */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card p-5"
        >
          <AlertsFeed 
            alerts={alerts}
            onAcknowledge={(id) => console.log('Acknowledge:', id)}
            onDismiss={(id) => console.log('Dismiss:', id)}
          />
        </motion.div>
      </div>
    </div>
  )
}
