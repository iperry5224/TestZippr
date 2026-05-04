import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Wrench,
  Play,
  Copy,
  Check,
  AlertTriangle,
  Shield,
  Eye,
  Clock,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Terminal
} from 'lucide-react'

// Types
interface RemediationScript {
  id: string
  title: string
  description: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  control: string
  resourceType: string
  affectedResources: string[]
  script: string
  scriptType: 'aws-cli' | 'python' | 'cloudformation'
  estimatedImpact: string
  rollbackSteps: string
  status: 'pending' | 'approved' | 'executed' | 'failed'
  approvedBy?: string
  approvedAt?: string
  executedAt?: string
}

// Sample remediation scripts based on common Security Hub findings
const sampleRemediations: RemediationScript[] = [
  {
    id: 'rem-001',
    title: 'Block S3 Public Access',
    description: 'S3 buckets should block public access to prevent data exposure. This script enables the S3 Block Public Access settings.',
    severity: 'HIGH',
    control: 'AC-2',
    resourceType: 'AWS::S3::Bucket',
    affectedResources: ['slyk-view-656443597515-us-east-1'],
    script: `# Block public access for S3 bucket
aws s3api put-public-access-block \\
  --bucket BUCKET_NAME \\
  --public-access-block-configuration \\
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Verify the change
aws s3api get-public-access-block --bucket BUCKET_NAME`,
    scriptType: 'aws-cli',
    estimatedImpact: 'Blocks all public access to the bucket. Existing public objects will become private.',
    rollbackSteps: 'Run: aws s3api delete-public-access-block --bucket BUCKET_NAME',
    status: 'pending'
  },
  {
    id: 'rem-002',
    title: 'Enable S3 Server Access Logging',
    description: 'Enable server access logging to track requests made to S3 buckets for security auditing.',
    severity: 'MEDIUM',
    control: 'AU-6',
    resourceType: 'AWS::S3::Bucket',
    affectedResources: ['slyk-view-656443597515-us-east-1'],
    script: `# Create logging bucket if it doesn't exist
aws s3 mb s3://BUCKET_NAME-logs --region us-east-1

# Enable logging
aws s3api put-bucket-logging --bucket BUCKET_NAME \\
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "BUCKET_NAME-logs",
      "TargetPrefix": "access-logs/"
    }
  }'`,
    scriptType: 'aws-cli',
    estimatedImpact: 'Creates a logging bucket and enables access logging. May incur additional S3 storage costs.',
    rollbackSteps: 'Run: aws s3api put-bucket-logging --bucket BUCKET_NAME --bucket-logging-status {}',
    status: 'pending'
  },
  {
    id: 'rem-003',
    title: 'Enable S3 Default Encryption',
    description: 'Enable default server-side encryption for S3 buckets to protect data at rest.',
    severity: 'MEDIUM',
    control: 'CM-6',
    resourceType: 'AWS::S3::Bucket',
    affectedResources: ['slyk-view-656443597515-us-east-1'],
    script: `# Enable default encryption with AES-256
aws s3api put-bucket-encryption --bucket BUCKET_NAME \\
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Verify encryption is enabled
aws s3api get-bucket-encryption --bucket BUCKET_NAME`,
    scriptType: 'aws-cli',
    estimatedImpact: 'All new objects will be encrypted. Existing objects are not affected.',
    rollbackSteps: 'Run: aws s3api delete-bucket-encryption --bucket BUCKET_NAME',
    status: 'pending'
  },
  {
    id: 'rem-004',
    title: 'Enforce SSL/TLS for S3 Bucket',
    description: 'Add bucket policy to deny requests that do not use SSL/TLS encryption in transit.',
    severity: 'MEDIUM',
    control: 'CM-6',
    resourceType: 'AWS::S3::Bucket',
    affectedResources: ['slyk-view-656443597515-us-east-1'],
    script: `# Add policy to enforce SSL
aws s3api put-bucket-policy --bucket BUCKET_NAME --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "EnforceSSL",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": [
      "arn:aws:s3:::BUCKET_NAME",
      "arn:aws:s3:::BUCKET_NAME/*"
    ],
    "Condition": {
      "Bool": {
        "aws:SecureTransport": "false"
      }
    }
  }]
}'`,
    scriptType: 'aws-cli',
    estimatedImpact: 'All non-HTTPS requests will be denied. Ensure all applications use HTTPS.',
    rollbackSteps: 'Run: aws s3api delete-bucket-policy --bucket BUCKET_NAME',
    status: 'pending'
  },
  {
    id: 'rem-005',
    title: 'Enable CloudTrail Logging',
    description: 'Enable AWS CloudTrail to log all API calls for security monitoring and compliance.',
    severity: 'HIGH',
    control: 'AU-6',
    resourceType: 'AWS::CloudTrail::Trail',
    affectedResources: ['Account-wide'],
    script: `# Create S3 bucket for CloudTrail logs
aws s3 mb s3://cloudtrail-logs-$(aws sts get-caller-identity --query Account --output text)-us-east-1

# Create CloudTrail
aws cloudtrail create-trail \\
  --name slyk-security-trail \\
  --s3-bucket-name cloudtrail-logs-$(aws sts get-caller-identity --query Account --output text)-us-east-1 \\
  --is-multi-region-trail \\
  --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name slyk-security-trail`,
    scriptType: 'aws-cli',
    estimatedImpact: 'Creates a new CloudTrail that logs all API calls. S3 storage costs apply.',
    rollbackSteps: 'Run: aws cloudtrail delete-trail --name slyk-security-trail',
    status: 'pending'
  }
]

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e'
}

export default function Remediation() {
  const [remediations, setRemediations] = useState<RemediationScript[]>(sampleRemediations)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'executed'>('all')
  const [auditLog, setAuditLog] = useState<Array<{action: string, item: string, time: string, user: string}>>([])

  const filteredRemediations = remediations.filter(r => 
    filter === 'all' || r.status === filter
  )

  const handleCopyScript = (id: string, script: string) => {
    navigator.clipboard.writeText(script)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
    
    // Add to audit log
    const rem = remediations.find(r => r.id === id)
    if (rem) {
      setAuditLog(prev => [{
        action: 'Copied Script',
        item: rem.title,
        time: new Date().toLocaleString(),
        user: 'ira.perry@noaa.gov'
      }, ...prev])
    }
  }

  const handleApprove = (id: string) => {
    setRemediations(prev => prev.map(r => 
      r.id === id ? {
        ...r,
        status: 'approved' as const,
        approvedBy: 'ira.perry@noaa.gov',
        approvedAt: new Date().toISOString()
      } : r
    ))
    
    const rem = remediations.find(r => r.id === id)
    if (rem) {
      setAuditLog(prev => [{
        action: 'Approved',
        item: rem.title,
        time: new Date().toLocaleString(),
        user: 'ira.perry@noaa.gov'
      }, ...prev])
    }
  }

  const handleExecute = (id: string) => {
    // In production, this would call the Lambda to execute the script
    setRemediations(prev => prev.map(r => 
      r.id === id ? {
        ...r,
        status: 'executed' as const,
        executedAt: new Date().toISOString()
      } : r
    ))
    
    const rem = remediations.find(r => r.id === id)
    if (rem) {
      setAuditLog(prev => [{
        action: 'Executed',
        item: rem.title,
        time: new Date().toLocaleString(),
        user: 'ira.perry@noaa.gov'
      }, ...prev])
    }
  }

  const pendingCount = remediations.filter(r => r.status === 'pending').length
  const approvedCount = remediations.filter(r => r.status === 'approved').length
  const executedCount = remediations.filter(r => r.status === 'executed').length

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
              <Wrench className="w-8 h-8 text-slyk-primary" />
              Remediation
            </h1>
            <p className="text-dark-muted mt-1">
              Review and approve security fixes with human-in-the-loop control
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-xl">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Human Approval Required</span>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border cursor-pointer transition-all ${
              filter === 'all' ? 'border-slyk-primary' : 'border-dark-border/50 hover:border-dark-border'
            }`}
            onClick={() => setFilter('all')}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Total Scripts</p>
                <p className="text-3xl font-bold text-dark-text mt-1">{remediations.length}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-slyk-primary/20 flex items-center justify-center">
                <Terminal className="w-6 h-6 text-slyk-primary" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className={`bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border cursor-pointer transition-all ${
              filter === 'pending' ? 'border-yellow-500' : 'border-dark-border/50 hover:border-dark-border'
            }`}
            onClick={() => setFilter('pending')}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Pending Review</p>
                <p className="text-3xl font-bold text-yellow-500 mt-1">{pendingCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className={`bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border cursor-pointer transition-all ${
              filter === 'approved' ? 'border-blue-500' : 'border-dark-border/50 hover:border-dark-border'
            }`}
            onClick={() => setFilter('approved')}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Approved</p>
                <p className="text-3xl font-bold text-blue-500 mt-1">{approvedCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Check className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className={`bg-dark-card/50 backdrop-blur-sm rounded-2xl p-6 border cursor-pointer transition-all ${
              filter === 'executed' ? 'border-green-500' : 'border-dark-border/50 hover:border-dark-border'
            }`}
            onClick={() => setFilter('executed')}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-muted text-sm">Executed</p>
                <p className="text-3xl font-bold text-green-500 mt-1">{executedCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Remediation Scripts */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-semibold text-dark-text">Remediation Scripts</h2>
            
            <AnimatePresence>
              {filteredRemediations.map((rem, index) => (
                <motion.div
                  key={rem.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-dark-card/50 backdrop-blur-sm rounded-2xl border border-dark-border/50 overflow-hidden"
                >
                  {/* Header */}
                  <div
                    className="p-4 cursor-pointer hover:bg-dark-border/20 transition-colors"
                    onClick={() => setExpandedId(expandedId === rem.id ? null : rem.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: SEVERITY_COLORS[rem.severity] }}
                        />
                        <div>
                          <h3 className="font-semibold text-dark-text">{rem.title}</h3>
                          <p className="text-sm text-dark-muted">
                            {rem.control} • {rem.resourceType}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          rem.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                          rem.status === 'approved' ? 'bg-blue-500/20 text-blue-400' :
                          rem.status === 'executed' ? 'bg-green-500/20 text-green-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {rem.status.charAt(0).toUpperCase() + rem.status.slice(1)}
                        </span>
                        {expandedId === rem.id ? (
                          <ChevronUp className="w-5 h-5 text-dark-muted" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-dark-muted" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {expandedId === rem.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-dark-border/50"
                      >
                        <div className="p-4 space-y-4">
                          {/* Description */}
                          <div>
                            <h4 className="text-sm font-medium text-dark-muted mb-1">Description</h4>
                            <p className="text-dark-text">{rem.description}</p>
                          </div>

                          {/* Affected Resources */}
                          <div>
                            <h4 className="text-sm font-medium text-dark-muted mb-1">Affected Resources</h4>
                            <div className="flex flex-wrap gap-2">
                              {rem.affectedResources.map((resource, i) => (
                                <span key={i} className="px-2 py-1 bg-dark-border/50 rounded text-sm text-dark-text">
                                  {resource}
                                </span>
                              ))}
                            </div>
                          </div>

                          {/* Script Preview */}
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="text-sm font-medium text-dark-muted">Script ({rem.scriptType})</h4>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleCopyScript(rem.id, rem.script)
                                }}
                                className="flex items-center gap-1 text-sm text-slyk-primary hover:text-slyk-secondary transition-colors"
                              >
                                {copiedId === rem.id ? (
                                  <>
                                    <Check className="w-4 h-4" />
                                    Copied!
                                  </>
                                ) : (
                                  <>
                                    <Copy className="w-4 h-4" />
                                    Copy Script
                                  </>
                                )}
                              </button>
                            </div>
                            <pre className="bg-dark-bg p-4 rounded-xl text-sm text-green-400 overflow-x-auto font-mono">
                              {rem.script}
                            </pre>
                          </div>

                          {/* Impact & Rollback */}
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="text-sm font-medium text-dark-muted mb-1">Estimated Impact</h4>
                              <p className="text-sm text-dark-text">{rem.estimatedImpact}</p>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium text-dark-muted mb-1">Rollback Steps</h4>
                              <p className="text-sm text-dark-text">{rem.rollbackSteps}</p>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-3 pt-2 border-t border-dark-border/50">
                            {rem.status === 'pending' && (
                              <>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleApprove(rem.id)
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl hover:bg-blue-500/30 transition-colors"
                                >
                                  <Check className="w-4 h-4" />
                                  Approve
                                </button>
                                <span className="text-sm text-dark-muted">
                                  Review the script before approving
                                </span>
                              </>
                            )}
                            {rem.status === 'approved' && (
                              <>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleExecute(rem.id)
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-xl hover:bg-green-500/30 transition-colors"
                                >
                                  <Play className="w-4 h-4" />
                                  Execute Now
                                </button>
                                <span className="text-sm text-dark-muted">
                                  Approved by {rem.approvedBy} at {new Date(rem.approvedAt!).toLocaleString()}
                                </span>
                              </>
                            )}
                            {rem.status === 'executed' && (
                              <span className="flex items-center gap-2 text-green-400">
                                <CheckCircle className="w-5 h-5" />
                                Executed at {new Date(rem.executedAt!).toLocaleString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Audit Log */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-dark-text">Audit Log</h2>
            <div className="bg-dark-card/50 backdrop-blur-sm rounded-2xl border border-dark-border/50 p-4">
              {auditLog.length === 0 ? (
                <div className="text-center py-8 text-dark-muted">
                  <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No actions yet</p>
                  <p className="text-sm">Actions will be logged here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {auditLog.map((log, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-start gap-3 p-3 bg-dark-bg/50 rounded-xl"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        log.action === 'Executed' ? 'bg-green-500/20' :
                        log.action === 'Approved' ? 'bg-blue-500/20' :
                        'bg-gray-500/20'
                      }`}>
                        {log.action === 'Executed' ? (
                          <Play className="w-4 h-4 text-green-400" />
                        ) : log.action === 'Approved' ? (
                          <Check className="w-4 h-4 text-blue-400" />
                        ) : (
                          <Copy className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-dark-text truncate">
                          {log.action}: {log.item}
                        </p>
                        <p className="text-xs text-dark-muted">
                          {log.user} • {log.time}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-slyk-primary/10 border border-slyk-primary/30 rounded-2xl p-4">
              <h3 className="font-semibold text-slyk-primary flex items-center gap-2 mb-2">
                <Shield className="w-5 h-5" />
                Human-in-the-Loop
              </h3>
              <p className="text-sm text-dark-muted">
                All remediation scripts require manual review and approval before execution. 
                This ensures you maintain full control over changes to your AWS environment.
              </p>
              <ul className="mt-3 space-y-1 text-sm text-dark-muted">
                <li className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-slyk-primary" />
                  Review script before approval
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-400" />
                  Approve to enable execution
                </li>
                <li className="flex items-center gap-2">
                  <Play className="w-4 h-4 text-green-400" />
                  Execute when ready
                </li>
              </ul>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
