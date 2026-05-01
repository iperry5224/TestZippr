import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'
import clsx from 'clsx'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  onSendMessage?: (message: string) => Promise<string>
  suggestedPrompts?: string[]
  placeholder?: string
}

const defaultPrompts = [
  "Assess my AC-2 compliance",
  "Run a full security assessment",
  "Generate remediation for CM-6",
  "What's my current compliance score?",
  "Harden my S3 buckets",
  "Show me critical findings"
]

export default function ChatInterface({
  onSendMessage,
  suggestedPrompts = defaultPrompts,
  placeholder = "Ask SLyK anything about your security posture..."
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Simulate API call or use actual Bedrock agent
      const response = onSendMessage 
        ? await onSendMessage(userMessage.content)
        : await simulateResponse(userMessage.content)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const simulateResponse = async (input: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    if (input.toLowerCase().includes('assess')) {
      return `## Assessment Results

I've completed a security assessment of your environment. Here's the summary:

**Overall Compliance: 78%**

| Control | Status | Findings |
|---------|--------|----------|
| AC-2 | ⚠️ WARNING | 3 users without MFA |
| AU-6 | ✅ PASS | Audit logging configured |
| CM-6 | ❌ FAIL | 2 EC2 instances need IMDSv2 |
| SI-2 | ⚠️ WARNING | 5 patches pending |
| RA-5 | ✅ PASS | 95% scan coverage |

Would you like me to generate remediation scripts for the failed controls?`
    }

    if (input.toLowerCase().includes('remediat')) {
      return `## Remediation Playbook Generated

I've created remediation scripts for the identified issues:

### CM-6: Configuration Settings

\`\`\`bash
# Enforce IMDSv2 on EC2 instances
aws ec2 modify-instance-metadata-options \\
  --instance-id i-0abc123def456 \\
  --http-tokens required \\
  --http-endpoint enabled
\`\`\`

### AC-2: Account Management

\`\`\`bash
# Tag untagged users
aws iam tag-user --user-name john.doe \\
  --tags Key=Owner,Value=IT-Security
\`\`\`

Would you like me to execute these scripts?`
    }

    return `I can help you with:

1. **Assess** - Run NIST 800-53 compliance assessments
2. **Remediate** - Generate and execute remediation scripts
3. **Harden** - Scan and secure AWS resources

What would you like to do?`
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', duration: 0.5 }}
              className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slyk-primary to-slyk-secondary flex items-center justify-center mb-6 shadow-glow"
            >
              <Sparkles className="w-10 h-10 text-white" />
            </motion.div>
            <h2 className="text-2xl font-bold gradient-text mb-2">Ask SLyK</h2>
            <p className="text-dark-muted mb-8 max-w-md">
              Your AI security assistant for NIST 800-53 compliance, remediation, and hardening.
            </p>
            
            <div className="grid grid-cols-2 gap-3 max-w-lg">
              {suggestedPrompts.slice(0, 4).map((prompt, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  onClick={() => setInput(prompt)}
                  className="p-3 text-left text-sm rounded-xl bg-dark-card/50 border border-dark-border/50 hover:border-slyk-primary/50 hover:bg-dark-card transition-all"
                >
                  {prompt}
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={clsx(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slyk-primary to-slyk-secondary flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={clsx(
                  'max-w-[80%] rounded-2xl px-4 py-3',
                  message.role === 'user'
                    ? 'bg-slyk-primary text-white'
                    : 'bg-dark-card border border-dark-border/50'
                )}>
                  <div className={clsx(
                    'prose prose-sm max-w-none',
                    message.role === 'assistant' && 'prose-invert'
                  )}>
                    {message.content.split('\n').map((line, i) => (
                      <p key={i} className="mb-2 last:mb-0">{line}</p>
                    ))}
                  </div>
                  <span className={clsx(
                    'text-xs mt-2 block',
                    message.role === 'user' ? 'text-white/70' : 'text-dark-muted'
                  )}>
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-dark-text" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slyk-primary to-slyk-secondary flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-dark-card border border-dark-border/50 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-slyk-primary typing-dot" />
                <span className="w-2 h-2 rounded-full bg-slyk-primary typing-dot" />
                <span className="w-2 h-2 rounded-full bg-slyk-primary typing-dot" />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-dark-border/50">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className="flex-1 bg-dark-card border border-dark-border/50 rounded-xl px-4 py-3 resize-none focus:outline-none focus:border-slyk-primary/50 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={clsx(
              'px-4 rounded-xl transition-all',
              input.trim() && !isLoading
                ? 'bg-gradient-to-r from-slyk-primary to-slyk-secondary text-white shadow-glow hover:shadow-lg'
                : 'bg-dark-border text-dark-muted cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
