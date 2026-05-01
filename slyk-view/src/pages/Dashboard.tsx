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
import { useState } from 'react'

// Mock data - in production, this comes from the API
const complianceHistory = [
  { date: 'Mon', score: 72 },
  { date: 'Tue', score: 75 },
  { date: 'Wed', score: 73 },
  { date: 'Thu', score: 78 },
  { date: 'Fri', score: 76 },
  { date: 'Sat', score: 80 },
  { date: 'Sun', score: 82 },
]

const controlsData = [
  { 
    controlId: 'AC-2', 
    name: 'Account Management', 
    description: 'Automated detection of unauthorized account creation and MFA enforcement',
    status: 'WARNING' as const,
    findings: 3,
    lastChecked: '2 hours ago'
  },
  { 
    controlId: 'AU-6', 
    name: 'Audit Review & Analysis', 
    description: 'Real-time analysis of audit logs for anomalies and security events',
    status: 'PASS' as const,
    findings: 0,
    lastChecked: '2 hours ago'
  },
  { 
    controlId: 'CM-6', 
    name: 'Configuration Settings', 
    description: 'Automated verification of system configuration against baselines',
    status: 'FAIL' as const,
    findings: 5,
    lastChecked: '2 hours ago'
  },
  { 
    controlId: 'SI-2', 
    name: 'Flaw Remediation', 
    description: 'Automated remediation runbooks and patching logic',
    status: 'WARNING' as const,
    findings: 8,
    lastChecked: '2 hours ago'
  },
  { 
    controlId: 'RA-5', 
    name: 'Vulnerability Scanning', 
    description: 'Security scan coverage analysis relative to total inventory',
    status: 'PASS' as const,
    findings: 0,
    lastChecked: '2 hours ago'
  },
]

const alerts = [
  {
    id: '1',
    type: 'critical' as const,
    title: 'IMDSv2 Not Enforced',
    message: '2 EC2 instances are not using IMDSv2. This is a security risk that could allow SSRF attacks.',
    timestamp: '5 minutes ago',
    controlId: 'CM-6'
  },
  {
    id: '2',
    type: 'warning' as const,
    title: 'Users Without MFA',
    message: '3 IAM users do not have MFA enabled. Consider enforcing MFA for all users.',
    timestamp: '1 hour ago',
    controlId: 'AC-2'
  },
  {
    id: '3',
    type: 'warning' as const,
    title: 'Pending Patches',
    message: '8 instances have critical patches pending installation.',
    timestamp: '3 hours ago',
    controlId: 'SI-2'
  },
]

const statusDistribution = [
  { name: 'Pass', value: 2, color: '#10B981' },
  { name: 'Warning', value: 2, color: '#F59E0B' },
  { name: 'Fail', value: 1, color: '#EF4444' },
]

export default function Dashboard() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const complianceScore = 78
  const previousScore = 72

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsRefreshing(false)
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
            Security Dashboard
          </motion.h1>
          <p className="text-dark-muted mt-1">
            NIST 800-53 Compliance Overview
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-dark-muted">
            <Clock className="w-4 h-4" />
            Last updated: 2 hours ago
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
              <p className="text-3xl font-bold text-dark-text mt-1">5</p>
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
              <p className="text-3xl font-bold text-slyk-success mt-1">2</p>
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
              <p className="text-3xl font-bold text-slyk-warning mt-1">2</p>
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
              <p className="text-3xl font-bold text-slyk-danger mt-1">1</p>
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
              {complianceScore > previousScore ? (
                <>
                  <TrendingUp className="w-5 h-5 text-slyk-success" />
                  <span className="text-slyk-success">
                    +{complianceScore - previousScore}% from last week
                  </span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-5 h-5 text-slyk-danger" />
                  <span className="text-slyk-danger">
                    {complianceScore - previousScore}% from last week
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
