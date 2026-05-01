import { motion } from 'framer-motion'
import { useParams } from 'react-router-dom'
import { 
  Shield, 
  Play, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  ChevronRight,
  Download,
  Wrench
} from 'lucide-react'
import ControlCard from '../components/ControlCard'
import { useState } from 'react'
import clsx from 'clsx'

const controlsData = {
  'AC-2': {
    controlId: 'AC-2',
    name: 'Account Management',
    family: 'Access Control',
    description: 'Automated detection of unauthorized account creation, MFA enforcement, and ownership tagging.',
    status: 'WARNING' as const,
    findings: [
      { id: 1, severity: 'high', title: '3 users without MFA enabled', resource: 'IAM Users', recommendation: 'Enable MFA for all IAM users' },
      { id: 2, severity: 'medium', title: '5 users without ownership tags', resource: 'IAM Users', recommendation: 'Add Owner tag to all users' },
      { id: 3, severity: 'low', title: '2 users created in last 7 days', resource: 'IAM Users', recommendation: 'Review recently created accounts' },
    ],
    checks: [
      { name: 'MFA Enforcement', status: 'fail', detail: '3 of 15 users without MFA' },
      { name: 'Ownership Tagging', status: 'fail', detail: '5 users missing Owner tag' },
      { name: 'Recent Account Review', status: 'warning', detail: '2 accounts created recently' },
      { name: 'Access Key Rotation', status: 'pass', detail: 'All keys < 90 days old' },
    ],
    lastAssessed: '2 hours ago',
    nextScheduled: 'Tomorrow 7:30 AM',
  },
  'AU-6': {
    controlId: 'AU-6',
    name: 'Audit Review, Analysis, and Reporting',
    family: 'Audit and Accountability',
    description: 'Real-time analysis of audit logs for anomalies, failed logins, and sensitive API activity.',
    status: 'PASS' as const,
    findings: [],
    checks: [
      { name: 'CloudTrail Enabled', status: 'pass', detail: 'Multi-region trail active' },
      { name: 'Log File Validation', status: 'pass', detail: 'Integrity validation enabled' },
      { name: 'Failed Login Monitoring', status: 'pass', detail: '0 suspicious patterns' },
      { name: 'Root Account Activity', status: 'pass', detail: 'No root activity in 30 days' },
    ],
    lastAssessed: '2 hours ago',
    nextScheduled: 'Tomorrow 7:30 AM',
  },
  'CM-6': {
    controlId: 'CM-6',
    name: 'Configuration Settings',
    family: 'Configuration Management',
    description: 'Automated verification of system configuration against established baselines.',
    status: 'FAIL' as const,
    findings: [
      { id: 1, severity: 'critical', title: '2 EC2 instances without IMDSv2', resource: 'i-0abc123, i-0def456', recommendation: 'Enable IMDSv2 on all instances' },
      { id: 2, severity: 'high', title: '3 S3 buckets without encryption', resource: 'my-bucket-1, my-bucket-2', recommendation: 'Enable default encryption' },
      { id: 3, severity: 'medium', title: '1 security group open to 0.0.0.0/0', resource: 'sg-12345', recommendation: 'Restrict to specific CIDRs' },
    ],
    checks: [
      { name: 'IMDSv2 Enforcement', status: 'fail', detail: '2 instances non-compliant' },
      { name: 'S3 Encryption', status: 'fail', detail: '3 buckets unencrypted' },
      { name: 'Security Group Rules', status: 'warning', detail: '1 overly permissive rule' },
      { name: 'EBS Encryption Default', status: 'pass', detail: 'Enabled account-wide' },
    ],
    lastAssessed: '2 hours ago',
    nextScheduled: 'Tomorrow 7:30 AM',
  },
  'SI-2': {
    controlId: 'SI-2',
    name: 'Flaw Remediation',
    family: 'System and Information Integrity',
    description: 'Automated generation of remediation runbooks and patching logic.',
    status: 'WARNING' as const,
    findings: [
      { id: 1, severity: 'high', title: '5 instances with critical patches pending', resource: 'EC2 Fleet', recommendation: 'Apply patches via SSM' },
      { id: 2, severity: 'medium', title: '3 instances with high severity patches', resource: 'EC2 Fleet', recommendation: 'Schedule maintenance window' },
    ],
    checks: [
      { name: 'SSM Patch Compliance', status: 'warning', detail: '8 patches pending' },
      { name: 'Inspector Findings', status: 'pass', detail: '0 critical vulnerabilities' },
      { name: 'Maintenance Windows', status: 'pass', detail: 'Weekly window configured' },
    ],
    lastAssessed: '2 hours ago',
    nextScheduled: 'Tomorrow 7:30 AM',
  },
  'RA-5': {
    controlId: 'RA-5',
    name: 'Vulnerability Monitoring and Scanning',
    family: 'Risk Assessment',
    description: 'Analyzing security scan percentages relative to the total system inventory.',
    status: 'PASS' as const,
    findings: [],
    checks: [
      { name: 'SSM Coverage', status: 'pass', detail: '95% of instances managed' },
      { name: 'Inspector Coverage', status: 'pass', detail: '100% EC2 coverage' },
      { name: 'ECR Scanning', status: 'pass', detail: 'All repositories scanned' },
      { name: 'Lambda Scanning', status: 'pass', detail: 'All functions covered' },
    ],
    lastAssessed: '2 hours ago',
    nextScheduled: 'Tomorrow 7:30 AM',
  },
}

const severityColors = {
  critical: 'text-slyk-danger bg-slyk-danger/20 border-slyk-danger/30',
  high: 'text-orange-400 bg-orange-400/20 border-orange-400/30',
  medium: 'text-slyk-warning bg-slyk-warning/20 border-slyk-warning/30',
  low: 'text-slyk-accent bg-slyk-accent/20 border-slyk-accent/30',
}

const statusIcons = {
  pass: CheckCircle,
  fail: XCircle,
  warning: AlertTriangle,
}

const statusColors = {
  pass: 'text-slyk-success',
  fail: 'text-slyk-danger',
  warning: 'text-slyk-warning',
}

export default function Controls() {
  const { controlId } = useParams()
  const [isRunning, setIsRunning] = useState(false)

  const handleRunAssessment = async () => {
    setIsRunning(true)
    await new Promise(resolve => setTimeout(resolve, 3000))
    setIsRunning(false)
  }

  if (controlId && controlsData[controlId as keyof typeof controlsData]) {
    const control = controlsData[controlId as keyof typeof controlsData]
    
    return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-sm font-mono text-slyk-primary">{control.controlId}</span>
              <span className="text-sm text-dark-muted">•</span>
              <span className="text-sm text-dark-muted">{control.family}</span>
            </div>
            <h1 className="text-3xl font-bold text-dark-text">{control.name}</h1>
            <p className="text-dark-muted mt-2 max-w-2xl">{control.description}</p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleRunAssessment}
              disabled={isRunning}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary text-white hover:bg-slyk-primary/90 transition-colors disabled:opacity-50"
            >
              <Play className={`w-4 h-4 ${isRunning ? 'animate-pulse' : ''}`} />
              {isRunning ? 'Running...' : 'Run Assessment'}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-card border border-dark-border text-dark-text hover:bg-dark-border/50 transition-colors">
              <Wrench className="w-4 h-4" />
              Remediate
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-card border border-dark-border text-dark-text hover:bg-dark-border/50 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5"
          >
            <p className="text-dark-muted text-sm">Status</p>
            <div className="flex items-center gap-2 mt-2">
              {control.status === 'PASS' && <CheckCircle className="w-6 h-6 text-slyk-success" />}
              {control.status === 'FAIL' && <XCircle className="w-6 h-6 text-slyk-danger" />}
              {control.status === 'WARNING' && <AlertTriangle className="w-6 h-6 text-slyk-warning" />}
              <span className={clsx(
                'text-2xl font-bold',
                control.status === 'PASS' && 'text-slyk-success',
                control.status === 'FAIL' && 'text-slyk-danger',
                control.status === 'WARNING' && 'text-slyk-warning',
              )}>
                {control.status}
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-5"
          >
            <p className="text-dark-muted text-sm">Last Assessed</p>
            <p className="text-2xl font-bold text-dark-text mt-2">{control.lastAssessed}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-5"
          >
            <p className="text-dark-muted text-sm">Next Scheduled</p>
            <p className="text-2xl font-bold text-dark-text mt-2">{control.nextScheduled}</p>
          </motion.div>
        </div>

        {/* Checks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <h2 className="text-lg font-semibold text-dark-text mb-4">Assessment Checks</h2>
          <div className="space-y-3">
            {control.checks.map((check, index) => {
              const Icon = statusIcons[check.status as keyof typeof statusIcons]
              return (
                <div 
                  key={index}
                  className="flex items-center justify-between p-4 rounded-xl bg-dark-bg/50 border border-dark-border/30"
                >
                  <div className="flex items-center gap-3">
                    <Icon className={clsx('w-5 h-5', statusColors[check.status as keyof typeof statusColors])} />
                    <span className="font-medium text-dark-text">{check.name}</span>
                  </div>
                  <span className="text-sm text-dark-muted">{check.detail}</span>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* Findings */}
        {control.findings.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card p-6"
          >
            <h2 className="text-lg font-semibold text-dark-text mb-4">
              Findings ({control.findings.length})
            </h2>
            <div className="space-y-3">
              {control.findings.map((finding) => (
                <div 
                  key={finding.id}
                  className="p-4 rounded-xl bg-dark-bg/50 border border-dark-border/30"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={clsx(
                          'px-2 py-0.5 rounded text-xs font-medium border',
                          severityColors[finding.severity as keyof typeof severityColors]
                        )}>
                          {finding.severity.toUpperCase()}
                        </span>
                        <span className="text-sm text-dark-muted">{finding.resource}</span>
                      </div>
                      <h4 className="font-medium text-dark-text">{finding.title}</h4>
                      <p className="text-sm text-dark-muted mt-1">{finding.recommendation}</p>
                    </div>
                    <button className="text-slyk-primary hover:underline text-sm">
                      Remediate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    )
  }

  // Controls list view
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold gradient-text">Security Controls</h1>
        <p className="text-dark-muted mt-1">NIST 800-53 Control Assessment Status</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.values(controlsData).map((control) => (
          <ControlCard
            key={control.controlId}
            controlId={control.controlId}
            name={control.name}
            description={control.description}
            status={control.status}
            findings={control.findings.length}
            lastChecked={control.lastAssessed}
          />
        ))}
      </div>
    </div>
  )
}
