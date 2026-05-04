import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Shield,
  ShieldAlert,
  MessageSquare,
  Server,
  Wrench,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap
} from 'lucide-react'
import clsx from 'clsx'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/controls', icon: Shield, label: 'Controls' },
  { path: '/securityhub', icon: ShieldAlert, label: 'Security Hub' },
  { path: '/chat', icon: MessageSquare, label: 'Ask SLyK' },
  { path: '/inventory', icon: Server, label: 'Inventory' },
  { path: '/remediation', icon: Wrench, label: 'Remediation' },
  { path: '/reports', icon: FileText, label: 'Reports' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 256 }}
      className="fixed left-0 top-0 h-screen bg-dark-card/50 backdrop-blur-xl border-r border-dark-border/50 z-50 flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-dark-border/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slyk-primary to-slyk-secondary flex items-center justify-center shadow-glow">
            <Zap className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h1 className="text-xl font-bold gradient-text">SLyK-View</h1>
              <p className="text-xs text-dark-muted">Security Dashboard</p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200',
                isActive
                  ? 'bg-slyk-primary/20 text-slyk-primary shadow-glow'
                  : 'text-dark-muted hover:text-dark-text hover:bg-dark-border/30'
              )
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="font-medium"
              >
                {item.label}
              </motion.span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-dark-border/50">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-dark-muted hover:text-dark-text hover:bg-dark-border/30 transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>

      {/* Version */}
      {!collapsed && (
        <div className="px-4 py-3 text-xs text-dark-muted border-t border-dark-border/50">
          <p>SLyK-View v1.0.0</p>
          <p>GRCP Platform</p>
        </div>
      )}
    </motion.aside>
  )
}
