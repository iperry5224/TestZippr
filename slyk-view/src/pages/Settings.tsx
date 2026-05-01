import { motion } from 'framer-motion'
import { useState } from 'react'
import { 
  Settings as SettingsIcon, 
  User, 
  Bell, 
  Shield, 
  Cloud,
  Save,
  Copy,
  Check
} from 'lucide-react'
import { useTenant } from '../context/TenantContext'
import clsx from 'clsx'

export default function Settings() {
  const { tenant, setTenant } = useTenant()
  const [activeTab, setActiveTab] = useState('tenant')
  const [copied, setCopied] = useState(false)
  const [formData, setFormData] = useState({
    tenantName: tenant?.name || '',
    awsAccountId: tenant?.awsAccountId || '',
    region: tenant?.region || 'us-east-1',
    agentId: tenant?.agentId || '',
    agentAliasId: tenant?.agentAliasId || '',
    notificationEmail: 'ira.perry@noaa.gov',
    dailyReportTime: '07:30',
    enableAlerts: true,
    enableDailyReport: true,
  })

  const handleSave = () => {
    setTenant({
      ...tenant!,
      name: formData.tenantName,
      awsAccountId: formData.awsAccountId,
      region: formData.region,
      agentId: formData.agentId,
      agentAliasId: formData.agentAliasId,
    })
  }

  const handleCopyConfig = () => {
    const config = JSON.stringify({
      tenant: formData.tenantName,
      awsAccountId: formData.awsAccountId,
      region: formData.region,
      agentId: formData.agentId,
      agentAliasId: formData.agentAliasId,
    }, null, 2)
    navigator.clipboard.writeText(config)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const tabs = [
    { key: 'tenant', label: 'Tenant Configuration', icon: Cloud },
    { key: 'notifications', label: 'Notifications', icon: Bell },
    { key: 'security', label: 'Security', icon: Shield },
    { key: 'profile', label: 'Profile', icon: User },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold gradient-text">Settings</h1>
        <p className="text-dark-muted mt-1">Configure SLyK-View for your organization</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-64 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left',
                activeTab === tab.key
                  ? 'bg-slyk-primary/20 text-slyk-primary'
                  : 'text-dark-muted hover:text-dark-text hover:bg-dark-border/30'
              )}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'tenant' && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card p-6 space-y-6"
            >
              <div>
                <h2 className="text-xl font-semibold text-dark-text mb-2">Tenant Configuration</h2>
                <p className="text-dark-muted text-sm">
                  Configure your AWS account and Bedrock agent settings. Share this configuration with other ISSOs to deploy SLyK-View in their tenants.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    Tenant Name
                  </label>
                  <input
                    type="text"
                    value={formData.tenantName}
                    onChange={(e) => setFormData({ ...formData, tenantName: e.target.value })}
                    placeholder="e.g., NESDIS NCIS"
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    AWS Account ID
                  </label>
                  <input
                    type="text"
                    value={formData.awsAccountId}
                    onChange={(e) => setFormData({ ...formData, awsAccountId: e.target.value })}
                    placeholder="123456789012"
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    AWS Region
                  </label>
                  <select
                    value={formData.region}
                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50"
                  >
                    <option value="us-east-1">US East (N. Virginia)</option>
                    <option value="us-west-2">US West (Oregon)</option>
                    <option value="eu-west-1">EU (Ireland)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    Bedrock Agent ID
                  </label>
                  <input
                    type="text"
                    value={formData.agentId}
                    onChange={(e) => setFormData({ ...formData, agentId: e.target.value })}
                    placeholder="XXXXXXXXXX"
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50 font-mono"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    Bedrock Agent Alias ID
                  </label>
                  <input
                    type="text"
                    value={formData.agentAliasId}
                    onChange={(e) => setFormData({ ...formData, agentAliasId: e.target.value })}
                    placeholder="XXXXXXXXXX"
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50 font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-4 border-t border-dark-border/50">
                <button
                  onClick={handleSave}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary text-white hover:bg-slyk-primary/90 transition-colors"
                >
                  <Save className="w-4 h-4" />
                  Save Configuration
                </button>
                <button
                  onClick={handleCopyConfig}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-border text-dark-text hover:bg-dark-border/70 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-slyk-success" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy Config
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 rounded-xl bg-slyk-primary/10 border border-slyk-primary/30">
                <h3 className="font-medium text-slyk-primary mb-2">Share with Other ISSOs</h3>
                <p className="text-sm text-dark-muted">
                  To deploy SLyK-View in another tenant, share the configuration above. 
                  They'll need to run the deployment script in their AWS account and update 
                  the Agent ID and Alias ID with their own values.
                </p>
              </div>
            </motion.div>
          )}

          {activeTab === 'notifications' && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card p-6 space-y-6"
            >
              <div>
                <h2 className="text-xl font-semibold text-dark-text mb-2">Notification Settings</h2>
                <p className="text-dark-muted text-sm">
                  Configure email alerts and scheduled reports.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">
                    Notification Email
                  </label>
                  <input
                    type="email"
                    value={formData.notificationEmail}
                    onChange={(e) => setFormData({ ...formData, notificationEmail: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-xl focus:outline-none focus:border-slyk-primary/50"
                  />
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-dark-bg border border-dark-border">
                  <div>
                    <h4 className="font-medium text-dark-text">Security Alerts</h4>
                    <p className="text-sm text-dark-muted">Receive email alerts for critical findings</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={formData.enableAlerts}
                      onChange={(e) => setFormData({ ...formData, enableAlerts: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:bg-slyk-primary transition-colors"></div>
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-dark-bg border border-dark-border">
                  <div>
                    <h4 className="font-medium text-dark-text">Daily Compliance Report</h4>
                    <p className="text-sm text-dark-muted">Receive daily summary at {formData.dailyReportTime} ET</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <input
                      type="time"
                      value={formData.dailyReportTime}
                      onChange={(e) => setFormData({ ...formData, dailyReportTime: e.target.value })}
                      className="px-3 py-1 bg-dark-card border border-dark-border rounded-lg text-sm"
                    />
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={formData.enableDailyReport}
                        onChange={(e) => setFormData({ ...formData, enableDailyReport: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-dark-border rounded-full peer peer-checked:bg-slyk-primary transition-colors"></div>
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                    </label>
                  </div>
                </div>
              </div>

              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slyk-primary text-white hover:bg-slyk-primary/90 transition-colors"
              >
                <Save className="w-4 h-4" />
                Save Settings
              </button>
            </motion.div>
          )}

          {activeTab === 'security' && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card p-6"
            >
              <h2 className="text-xl font-semibold text-dark-text mb-4">Security Settings</h2>
              <p className="text-dark-muted">
                Security settings are managed through AWS IAM and Cognito. 
                Contact your AWS administrator to modify access controls.
              </p>
            </motion.div>
          )}

          {activeTab === 'profile' && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card p-6"
            >
              <h2 className="text-xl font-semibold text-dark-text mb-4">Profile</h2>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-slyk-primary/20 flex items-center justify-center">
                  <User className="w-8 h-8 text-slyk-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text">Ira Perry</h3>
                  <p className="text-dark-muted">ira.perry@noaa.gov</p>
                  <p className="text-sm text-slyk-primary">ISSO • NESDIS NCIS</p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
