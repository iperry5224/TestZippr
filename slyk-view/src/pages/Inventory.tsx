import { motion } from 'framer-motion'
import { useState } from 'react'
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
  Filter
} from 'lucide-react'
import clsx from 'clsx'

const inventoryData = {
  ec2: [
    { id: 'i-0abc123def456', name: 'web-server-1', status: 'compliant', issues: 0, type: 't3.medium' },
    { id: 'i-0def456ghi789', name: 'api-server-1', status: 'warning', issues: 2, type: 't3.large' },
    { id: 'i-0ghi789jkl012', name: 'db-server-1', status: 'non-compliant', issues: 3, type: 'r5.large' },
    { id: 'i-0jkl012mno345', name: 'worker-1', status: 'compliant', issues: 0, type: 't3.small' },
  ],
  s3: [
    { id: 'my-app-bucket', name: 'my-app-bucket', status: 'compliant', issues: 0, region: 'us-east-1' },
    { id: 'logs-bucket', name: 'logs-bucket', status: 'warning', issues: 1, region: 'us-east-1' },
    { id: 'backup-bucket', name: 'backup-bucket', status: 'non-compliant', issues: 2, region: 'us-east-1' },
  ],
  iam: [
    { id: 'admin-user', name: 'admin-user', status: 'compliant', issues: 0, type: 'User' },
    { id: 'dev-user-1', name: 'dev-user-1', status: 'warning', issues: 1, type: 'User' },
    { id: 'service-role', name: 'service-role', status: 'compliant', issues: 0, type: 'Role' },
    { id: 'lambda-role', name: 'lambda-role', status: 'compliant', issues: 0, type: 'Role' },
  ],
  rds: [
    { id: 'prod-db', name: 'prod-database', status: 'compliant', issues: 0, engine: 'PostgreSQL' },
    { id: 'dev-db', name: 'dev-database', status: 'warning', issues: 1, engine: 'MySQL' },
  ],
}

const resourceTypes = [
  { key: 'ec2', label: 'EC2 Instances', icon: Server, count: inventoryData.ec2.length },
  { key: 's3', label: 'S3 Buckets', icon: Database, count: inventoryData.s3.length },
  { key: 'iam', label: 'IAM Resources', icon: Users, count: inventoryData.iam.length },
  { key: 'rds', label: 'RDS Databases', icon: Cloud, count: inventoryData.rds.length },
]

const statusConfig = {
  compliant: { icon: CheckCircle, color: 'text-slyk-success', bg: 'bg-slyk-success/20' },
  warning: { icon: AlertTriangle, color: 'text-slyk-warning', bg: 'bg-slyk-warning/20' },
  'non-compliant': { icon: XCircle, color: 'text-slyk-danger', bg: 'bg-slyk-danger/20' },
}

export default function Inventory() {
  const [selectedType, setSelectedType] = useState('ec2')
  const [searchQuery, setSearchQuery] = useState('')

  const currentData = inventoryData[selectedType as keyof typeof inventoryData] || []
  const filteredData = currentData.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalResources = Object.values(inventoryData).flat().length
  const compliantCount = Object.values(inventoryData).flat().filter(r => r.status === 'compliant').length
  const warningCount = Object.values(inventoryData).flat().filter(r => r.status === 'warning').length
  const nonCompliantCount = Object.values(inventoryData).flat().filter(r => r.status === 'non-compliant').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold gradient-text">Resource Inventory</h1>
        <p className="text-dark-muted mt-1">Security posture by AWS resource</p>
      </div>

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
            </tr>
          </thead>
          <tbody>
            {filteredData.map((resource, index) => {
              const config = statusConfig[resource.status as keyof typeof statusConfig]
              const Icon = config.icon
              return (
                <motion.tr
                  key={resource.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="border-b border-dark-border/30 hover:bg-dark-border/20 transition-colors cursor-pointer"
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
                      <span className={clsx('text-sm capitalize', config.color)}>
                        {resource.status}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    {resource.issues > 0 ? (
                      <span className="text-slyk-danger">{resource.issues} issues</span>
                    ) : (
                      <span className="text-dark-muted">None</span>
                    )}
                  </td>
                  <td className="p-4 text-dark-muted text-sm">
                    {(resource as any).type || (resource as any).region || (resource as any).engine || '-'}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>

        {filteredData.length === 0 && (
          <div className="p-8 text-center text-dark-muted">
            No resources found matching your search.
          </div>
        )}
      </motion.div>
    </div>
  )
}
