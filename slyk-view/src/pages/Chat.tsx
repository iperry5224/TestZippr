import { motion } from 'framer-motion'
import ChatInterface from '../components/ChatInterface'

export default function Chat() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-full flex flex-col"
    >
      <div className="p-6 border-b border-dark-border/50">
        <h1 className="text-3xl font-bold gradient-text">Ask SLyK</h1>
        <p className="text-dark-muted mt-1">
          Your AI security assistant for compliance, remediation, and hardening
        </p>
      </div>
      
      <div className="flex-1 overflow-hidden">
        <ChatInterface />
      </div>
    </motion.div>
  )
}
