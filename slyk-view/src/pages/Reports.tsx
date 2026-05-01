import { motion } from 'framer-motion'
import { useState } from 'react'
import { 
  FileText, 
  Download, 
  Calendar, 
  Clock, 
  Mail,
  Plus,
  Trash2,
  Play
} from 'lucide-react'
import clsx from 'clsx'

const recentReports = [
  { 
    id: '1', 
    name: 'Weekly Compliance Summary', 
    type: 'Compliance', 
    date: '2024-01-15', 
    status: 'completed',
    size: '2.4 MB'
  },
  { 
    id: '2', 
    name: 'AC-2 Assessment Report', 
    type: 'Control', 
    date: '2024-01-14', 
    status: 'completed',
    size: '1.1 MB'
  },
  { 
    id: '3', 
    name: 'Remediation Runbook - CM-6', 
    type: 'Remediation', 
    date: '2024-01-13', 
    status: 'completed',
    size: '856 KB'
  },
  { 
    id: '4', 
    name: 'Monthly Executive Summary', 
    type: 'Executive', 
    date: '2024-01-01', 
    status: 'completed',
    size: '3.2 MB'
  },
]

const scheduledReports = [
  { 
    id: '1', 
    name: 'Daily Compliance Check', 
    schedule: 'Daily at 7:30 AM ET',
    recipients: ['ira.perry@noaa.gov'],
    enabled: true
  },
  { 
    id: '2', 
    name: 'Weekly Summary', 
    schedule: 'Every Monday at 8:00 AM ET',
    recipients: ['ira.perry@noaa.gov', 'security-team@noaa.gov'],
    enabled: true
  },
  { 
    id: '3', 
    name: 'Monthly Executive Report', 
    schedule: '1st of each month at 9:00 AM ET',
    recipients: ['ira.perry@noaa.gov', 'leadership@noaa.gov'],
    enabled: false
  },
]

const reportTemplates = [
  { id: 'compliance', name: 'Compliance Summary', description: 'Overall compliance status and trends' },
  { id: 'control', name: 'Control Assessment', description: 'Detailed assessment for a specific control' },
  { id: 'remediation', name: 'Remediation Runbook', description: 'Step-by-step remediation instructions' },
  { id: 'executive', name: 'Executive Summary', description: 'High-level overview for leadership' },
  { id: 'inventory', name: 'Resource Inventory', description: 'Complete resource security posture' },
]

export default function Reports() {
  const [activeTab, setActiveTab] = useState<'recent' | 'scheduled' | 'generate'>('recent')

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Reports</h1>
          <p className="text-dark-muted mt-1">Generate, schedule, and download security reports</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary text-white hover:bg-slyk-primary/90 transition-colors">
          <Plus className="w-4 h-4" />
          New Report
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-border/50 pb-2">
        {[
          { key: 'recent', label: 'Recent Reports', icon: FileText },
          { key: 'scheduled', label: 'Scheduled', icon: Calendar },
          { key: 'generate', label: 'Generate', icon: Play },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-t-xl transition-all',
              activeTab === tab.key
                ? 'bg-dark-card border border-dark-border border-b-0 text-dark-text'
                : 'text-dark-muted hover:text-dark-text'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Recent Reports */}
      {activeTab === 'recent' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {recentReports.map((report, index) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass-card p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slyk-primary/20 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-slyk-primary" />
                </div>
                <div>
                  <h3 className="font-medium text-dark-text">{report.name}</h3>
                  <div className="flex items-center gap-3 text-sm text-dark-muted mt-1">
                    <span>{report.type}</span>
                    <span>•</span>
                    <span>{report.date}</span>
                    <span>•</span>
                    <span>{report.size}</span>
                  </div>
                </div>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-border/50 text-dark-text hover:bg-dark-border transition-colors">
                <Download className="w-4 h-4" />
                Download
              </button>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Scheduled Reports */}
      {activeTab === 'scheduled' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {scheduledReports.map((report, index) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={clsx(
                'glass-card p-4',
                !report.enabled && 'opacity-60'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={clsx(
                    'w-12 h-12 rounded-xl flex items-center justify-center',
                    report.enabled ? 'bg-slyk-success/20' : 'bg-dark-border/50'
                  )}>
                    <Clock className={clsx(
                      'w-6 h-6',
                      report.enabled ? 'text-slyk-success' : 'text-dark-muted'
                    )} />
                  </div>
                  <div>
                    <h3 className="font-medium text-dark-text">{report.name}</h3>
                    <div className="flex items-center gap-3 text-sm text-dark-muted mt-1">
                      <Calendar className="w-4 h-4" />
                      <span>{report.schedule}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Mail className="w-4 h-4 text-dark-muted" />
                      <span className="text-sm text-dark-muted">
                        {report.recipients.join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={report.enabled} 
                      className="sr-only peer"
                      onChange={() => {}}
                    />
                    <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:bg-slyk-primary transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </label>
                  <button className="p-2 rounded-lg hover:bg-dark-border/50 text-dark-muted hover:text-slyk-danger transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}

          <button className="w-full p-4 rounded-xl border-2 border-dashed border-dark-border hover:border-slyk-primary/50 text-dark-muted hover:text-dark-text transition-colors flex items-center justify-center gap-2">
            <Plus className="w-5 h-5" />
            Schedule New Report
          </button>
        </motion.div>
      )}

      {/* Generate Report */}
      {activeTab === 'generate' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {reportTemplates.map((template, index) => (
            <motion.button
              key={template.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="glass-card p-6 text-left hover:border-slyk-primary/50 transition-all"
            >
              <div className="w-12 h-12 rounded-xl bg-slyk-primary/20 flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-slyk-primary" />
              </div>
              <h3 className="font-semibold text-dark-text">{template.name}</h3>
              <p className="text-sm text-dark-muted mt-2">{template.description}</p>
              <div className="mt-4 flex items-center gap-2 text-slyk-primary text-sm">
                <Play className="w-4 h-4" />
                Generate Now
              </div>
            </motion.button>
          ))}
        </motion.div>
      )}
    </div>
  )
}
