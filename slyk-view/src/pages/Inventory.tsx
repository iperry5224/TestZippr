import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { 
  Server, 
  Database, 
  Cloud, 
  Users, 
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  RefreshCw,
  Info
} from 'lucide-react'
import clsx from 'clsx'

// API Gateway endpoint
const API_URL = "https://zc06lwmk4j.execute-api.us-east-1.amazonaws.com/prod"

interface Resource {
  id: string
  name: string
  status: 'compliant' | 'warning' | 'non-compliant'
  issues: number
  issueDetails?: string[]
  type?: string
  region?: string
  engine?: string
  state?: string
  arn?: string
  created?: string
  instanceClass?: string
  engineVersion?: string
}

interface InventoryData {
  ec2: Resource[]
  s3: Resource[]
  iam: Resource[]
  rds: Resource[]
  summary?: {
    total: number
    compliant: number
    warning: number
    non_compliant: number
  }
}

const statusConfig = {
  compliant: { icon: CheckCircle, color: 'text-slyk-success', bg: 'bg-slyk-success/20', label: 'Compliant' },
  warning: { icon: AlertTriangle, color: 'text-slyk-warning', bg: 'bg-slyk-warning/20', label: 'Warning' },
  'non-compliant': { icon: XCircle, color: 'text-slyk-danger', bg: 'bg-slyk-danger/20', label: 'Non-Compliant' },
}

export default function Inventory() {
  const [selectedType, setSelectedType] = useState('ec2')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inventoryData, setInventoryData] = useState<InventoryData>({
    ec2: [],
    s3: [],
    iam: [],
    rds: []
  })
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null)

  const fetchInventory = async () => {
    try {
      setError(null)
      const response = await fetch(`${API_URL}/inventory`)
      if (!response.ok) throw new Error('Failed to fetch inventory')
      const data = await response.json()
      
      if (data.status === 'SUCCESS') {
        setInventoryData({
          ec2: data.ec2 || [],
          s3: data.s3 || [],
          iam: data.iam || [],
          rds: data.rds || []
        })
      }
    } catch (err) {
      console.error('Error fetching inventory:', err)
      setError('Failed to load inventory. Please try again.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchInventory()
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchInventory()
  }

  const resourceTypes = [
    { key: 'ec2', label: 'EC2 Instances', icon: Server, count: inventoryData.ec2.length },
    { key: 's3', label: 'S3 Buckets', icon: Database, count: inventoryData.s3.length },
    { key: 'iam', label: 'IAM Resources', icon: Users, count: inventoryData.iam.length },
    { key: 'rds', label: 'RDS Databases', icon: Cloud, count: inventoryData.rds.length },
  ]

  const currentData: Resource[] = inventoryData[selectedType as keyof InventoryData] || []
  const filteredData = currentData.filter((item: Resource) => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalResources = Object.values(inventoryData).flat().length
  const compliantCount = Object.values(inventoryData).flat().filter((r: Resource) => r.status === 'compliant').length
  const warningCount = Object.values(inventoryData).flat().filter((r: Resource) => r.status === 'warning').length
  const nonCompliantCount = Object.values(inventoryData).flat().filter((r: Resource) => r.status === 'non-compliant').length

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-slyk-primary animate-spin mx-auto mb-4" />
          <p className="text-dark-muted">Loading inventory from AWS...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Resource Inventory</h1>
          <p className="text-dark-muted mt-1">Security posture by AWS resource</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary/20 text-slyk-primary hover:bg-slyk-primary/30 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-slyk-danger/20 border border-slyk-danger/50 rounded-xl p-4 text-slyk-danger">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total Resources</p>
              <p className="text-3xl font-bold text-dark-text mt-1">{totalResources}</p>
            </div>
            <Shield className="w-8 h-8 text-slyk-primary" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Compliant</p>
              <p className="text-3xl font-bold text-slyk-success mt-1">{compliantCount}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-slyk-success" />
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
              <p className="text-dark-muted text-sm">Warnings</p>
              <p className="text-3xl font-bold text-slyk-warning mt-1">{warningCount}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-slyk-warning" />
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
              <p className="text-dark-muted text-sm">Non-Compliant</p>
              <p className="text-3xl font-bold text-slyk-danger mt-1">{nonCompliantCount}</p>
            </div>
            <XCircle className="w-8 h-8 text-slyk-danger" />
          </div>
        </motion.div>
      </div>

      {/* Resource Type Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {resourceTypes.map((type) => (
          <button
            key={type.key}
            onClick={() => setSelectedType(type.key)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap',
              selectedType === type.key
                ? 'bg-slyk-primary text-white'
                : 'bg-dark-card border border-dark-border text-dark-muted hover:text-dark-text'
            )}
          >
            <type.icon className="w-4 h-4" />
            {type.label}
            <span className={clsx(
              'px-2 py-0.5 rounded-full text-xs',
              selectedType === type.key
                ? 'bg-white/20'
                : 'bg-dark-border'
            )}>
              {type.count}
            </span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-muted" />
        <input
          type="text"
          placeholder="Search resources..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-dark-card border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50 transition-colors"
        />
      </div>

      {/* Resource Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card overflow-hidden"
      >
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-border/50">
              <th className="text-left p-4 text-dark-muted font-medium">Resource</th>
              <th className="text-left p-4 text-dark-muted font-medium">ID</th>
              <th className="text-left p-4 text-dark-muted font-medium">Status</th>
              <th className="text-left p-4 text-dark-muted font-medium">Issues</th>
              <th className="text-left p-4 text-dark-muted font-medium">Details</th>
              <th className="text-left p-4 text-dark-muted font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((resource: Resource, index: number) => {
              const config = statusConfig[resource.status as keyof typeof statusConfig]
              const Icon = config.icon
              return (
                <motion.tr
                  key={resource.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className="border-b border-dark-border/30 hover:bg-dark-border/20 transition-colors"
                >
                  <td className="p-4">
                    <span className="font-medium text-dark-text">{resource.name}</span>
                  </td>
                  <td className="p-4">
                    <span className="font-mono text-sm text-dark-muted">{resource.id}</span>
                  </td>
                  <td className="p-4">
                    <div className={clsx(
                      'inline-flex items-center gap-2 px-3 py-1 rounded-full',
                      config.bg
                    )}>
                      <Icon className={clsx('w-4 h-4', config.color)} />
                      <span className={clsx('text-sm', config.color)}>
                        {config.label}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    {resource.issues > 0 ? (
                      <span className="text-slyk-danger">{resource.issues} issue{resource.issues > 1 ? 's' : ''}</span>
                    ) : (
                      <span className="text-dark-muted">None</span>
                    )}
                  </td>
                  <td className="p-4 text-dark-muted text-sm">
                    {resource.type || resource.region || resource.engine || resource.state || '-'}
                  </td>
                  <td className="p-4">
                    {resource.issueDetails && resource.issueDetails.length > 0 && (
                      <button
                        onClick={() => setSelectedResource(resource)}
                        className="p-2 rounded-lg hover:bg-dark-border/30 transition-colors"
                        title="View details"
                      >
                        <Info className="w-4 h-4 text-dark-muted" />
                      </button>
                    )}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>

        {filteredData.length === 0 && (
          <div className="p-8 text-center text-dark-muted">
            {currentData.length === 0 
              ? `No ${selectedType.toUpperCase()} resources found in this account.`
              : 'No resources found matching your search.'}
          </div>
        )}
      </motion.div>

      {/* Issue Details Modal */}
      {selectedResource && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setSelectedResource(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-dark-card border border-dark-border rounded-2xl p-6 max-w-lg w-full mx-4"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold text-dark-text mb-2">{selectedResource.name}</h3>
            <p className="text-dark-muted text-sm mb-4 font-mono">{selectedResource.id}</p>
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-dark-muted">Security Issues:</h4>
              {selectedResource.issueDetails?.map((issue, i) => (
                <div key={i} className="flex items-start gap-2 p-3 bg-slyk-danger/10 border border-slyk-danger/20 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-slyk-danger mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-dark-text">{issue}</span>
                </div>
              ))}
            </div>
            
            <button
              onClick={() => setSelectedResource(null)}
              className="mt-6 w-full py-2 rounded-xl bg-dark-border hover:bg-dark-border/70 transition-colors text-dark-text"
            >
              Close
            </button>
          </motion.div>
        </div>
      )}
    </div>
  )
}
