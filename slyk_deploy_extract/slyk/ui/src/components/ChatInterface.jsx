import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import agentService from '../services/agent';
import storageService from '../services/storage';

const QUICK_ACTIONS = [
  { label: '🔍 Assess Compliance', action: 'Assess my NIST 800-53 compliance' },
  { label: '🪣 Harden S3', action: 'Scan and harden all my S3 buckets' },
  { label: '💻 Harden EC2', action: 'Scan and harden all my EC2 instances' },
  { label: '👤 Harden IAM', action: 'Scan and harden my IAM users' },
  { label: '🚨 Security Hub', action: 'Show me critical Security Hub findings' },
  { label: '📄 Generate SSP', action: 'Generate a System Security Plan for System 5065' },
];

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const sendMessage = async (messageText) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setStreamingMessage('');

    try {
      // Log the action
      storageService.logAuditEvent('CHAT', {
        action: 'send_message',
        sessionId: agentService.getSessionId(),
        metadata: { messageLength: text.length },
      }).catch(() => {}); // Don't block on audit logging

      // Send to agent with streaming
      const response = await agentService.sendMessage(text, (chunk, fullText) => {
        setStreamingMessage(fullText);
      });

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessage('');

      // Save session
      storageService.saveSession(agentService.getSessionId(), [...messages, userMessage, assistantMessage])
        .catch(() => {}); // Don't block on session save

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `⚠️ Error: ${error.message || 'Failed to communicate with SLyK agent. Please try again.'}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
      setStreamingMessage('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (action) => {
    sendMessage(action);
  };

  const startNewSession = () => {
    agentService.newSession();
    setMessages([]);
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.length === 0 && !streamingMessage && (
          <div className="welcome-message">
            <div className="welcome-icon">🛡️</div>
            <h2>Welcome to SLyK-53</h2>
            <p>I'm your AI security assistant. I can help you assess NIST 800-53 compliance, 
               harden AWS resources, and generate compliance documentation.</p>
            <div className="quick-actions" style={{ marginTop: '24px', justifyContent: 'center' }}>
              {QUICK_ACTIONS.map((qa, i) => (
                <button 
                  key={i} 
                  className="quick-action"
                  onClick={() => handleQuickAction(qa.action)}
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-header">
              <div className="message-avatar">
                {msg.role === 'assistant' ? '🛡️' : '👤'}
              </div>
              <span>{msg.role === 'assistant' ? 'SLyK' : 'You'}</span>
              <span style={{ marginLeft: 'auto', fontSize: '11px' }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className={`message-content ${msg.isError ? 'error' : ''}`}>
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    return inline ? (
                      <code className={className} {...props}>{children}</code>
                    ) : (
                      <pre><code className={className} {...props}>{children}</code></pre>
                    );
                  }
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {streamingMessage && (
          <div className="message assistant">
            <div className="message-header">
              <div className="message-avatar">🛡️</div>
              <span>SLyK</span>
            </div>
            <div className="message-content">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
            </div>
          </div>
        )}

        {isLoading && !streamingMessage && (
          <div className="message assistant">
            <div className="message-header">
              <div className="message-avatar">🛡️</div>
              <span>SLyK</span>
            </div>
            <div className="message-content">
              <div className="loading">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        {messages.length > 0 && (
          <div className="quick-actions">
            {QUICK_ACTIONS.slice(0, 4).map((qa, i) => (
              <button 
                key={i} 
                className="quick-action"
                onClick={() => handleQuickAction(qa.action)}
                disabled={isLoading}
              >
                {qa.label}
              </button>
            ))}
            <button 
              className="quick-action"
              onClick={startNewSession}
              disabled={isLoading}
              style={{ marginLeft: 'auto' }}
            >
              🔄 New Session
            </button>
          </div>
        )}
        
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask SLyK: 'Assess my compliance' or 'Harden my S3 buckets'..."
              disabled={isLoading}
              rows={1}
            />
          </div>
          <button 
            className="send-button"
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
          >
            ➤
          </button>
        </div>
      </div>

      <style jsx>{`
        .welcome-message {
          text-align: center;
          padding: 60px 20px;
          max-width: 600px;
          margin: 0 auto;
        }
        .welcome-icon {
          font-size: 64px;
          margin-bottom: 20px;
        }
        .welcome-message h2 {
          font-size: 28px;
          margin-bottom: 12px;
          color: var(--text-primary);
        }
        .welcome-message p {
          color: var(--text-secondary);
          font-size: 15px;
          line-height: 1.6;
        }
        .message-content.error {
          background: rgba(248, 113, 113, 0.1);
          border: 1px solid rgba(248, 113, 113, 0.3);
        }
      `}</style>
    </div>
  );
}

export default ChatInterface;
