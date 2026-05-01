import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import authService from './services/auth';
import config from './config';

function App() {
  const [activeView, setActiveView] = useState('chat');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [assessmentData, setAssessmentData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check if we have required config
      if (!config.identityPoolId && !config.agentId) {
        console.warn('SLyK config not set - running in demo mode');
        setConnectionStatus('demo');
        return;
      }

      // Try to get credentials
      await authService.getCredentials();
      setConnectionStatus('connected');
    } catch (err) {
      console.error('Failed to initialize:', err);
      setConnectionStatus('disconnected');
      setError(err.message);
    }
  };

  const renderContent = () => {
    switch (activeView) {
      case 'chat':
        return <ChatInterface />;
      case 'dashboard':
        return <Dashboard assessmentData={assessmentData} />;
      case 'assess':
        return (
          <div className="dashboard">
            <div className="data-table">
              <div className="data-table-header">
                <span className="data-table-title">NIST 800-53 Assessment</span>
              </div>
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <p style={{ marginBottom: '20px', color: 'var(--text-secondary)' }}>
                  Run a compliance assessment against your AWS environment.
                </p>
                <button 
                  className="quick-action" 
                  style={{ padding: '12px 24px', fontSize: '14px' }}
                  onClick={() => setActiveView('chat')}
                >
                  🔍 Start Assessment in Chat
                </button>
              </div>
            </div>
          </div>
        );
      case 'harden':
        return (
          <div className="dashboard">
            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              {[
                { icon: '🪣', title: 'S3 Buckets', desc: 'Encryption, versioning, public access' },
                { icon: '💻', title: 'EC2 Instances', desc: 'IMDSv2, security groups, IAM roles' },
                { icon: '👤', title: 'IAM Users', desc: 'MFA, access key rotation, policies' },
              ].map((item, i) => (
                <div key={i} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveView('chat')}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>{item.icon}</div>
                  <h3 style={{ marginBottom: '8px' }}>{item.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        );
      case 'remediate':
        return (
          <div className="dashboard">
            <div className="data-table">
              <div className="data-table-header">
                <span className="data-table-title">Remediation Playbooks</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Control</th>
                    <th>Title</th>
                    <th>Description</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { id: 'AC-2', title: 'Account Management', desc: 'Enable MFA for IAM users' },
                    { id: 'AC-6', title: 'Least Privilege', desc: 'Remove overly permissive policies' },
                    { id: 'AU-2', title: 'Event Logging', desc: 'Enable CloudTrail logging' },
                    { id: 'IA-2', title: 'Root MFA', desc: 'Enable MFA on root account' },
                    { id: 'SC-7', title: 'Boundary Protection', desc: 'Restrict security groups' },
                    { id: 'SC-28', title: 'Encryption at Rest', desc: 'Enable S3 default encryption' },
                    { id: 'SI-4', title: 'System Monitoring', desc: 'Enable GuardDuty' },
                  ].map((item, i) => (
                    <tr key={i}>
                      <td><code>{item.id}</code></td>
                      <td>{item.title}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{item.desc}</td>
                      <td>
                        <button 
                          className="quick-action" 
                          style={{ padding: '4px 10px', fontSize: '12px' }}
                          onClick={() => setActiveView('chat')}
                        >
                          Generate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      case 'reports':
        return (
          <div className="dashboard">
            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
              {[
                { icon: '📋', title: 'System Security Plan (SSP)', desc: 'Generate comprehensive SSP document' },
                { icon: '📝', title: 'POA&M', desc: 'Plan of Action and Milestones' },
                { icon: '📊', title: 'Risk Assessment Report', desc: 'Security risk analysis' },
                { icon: '📈', title: 'Executive Summary', desc: 'High-level compliance overview' },
              ].map((item, i) => (
                <div key={i} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveView('chat')}>
                  <div style={{ fontSize: '36px', marginBottom: '12px' }}>{item.icon}</div>
                  <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>{item.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        );
      case 'history':
        return (
          <div className="dashboard">
            <div className="data-table">
              <div className="data-table-header">
                <span className="data-table-title">Assessment History</span>
              </div>
              <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <p>No assessment history yet.</p>
                <p style={{ marginTop: '8px', fontSize: '13px' }}>Run an assessment to see results here.</p>
              </div>
            </div>
          </div>
        );
      case 'settings':
        return (
          <div className="dashboard">
            <div className="data-table">
              <div className="data-table-header">
                <span className="data-table-title">Settings</span>
              </div>
              <div style={{ padding: '20px' }}>
                <div style={{ marginBottom: '24px' }}>
                  <h4 style={{ marginBottom: '12px' }}>Connection</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`status-dot ${connectionStatus === 'connected' ? '' : 'disconnected'}`}></span>
                    <span>{connectionStatus === 'connected' ? 'Connected to SLyK Agent' : connectionStatus === 'demo' ? 'Demo Mode' : 'Disconnected'}</span>
                  </div>
                </div>
                <div style={{ marginBottom: '24px' }}>
                  <h4 style={{ marginBottom: '12px' }}>Configuration</h4>
                  <div style={{ fontFamily: 'monospace', fontSize: '13px', color: 'var(--text-secondary)' }}>
                    <div>Region: {config.region}</div>
                    <div>Agent ID: {config.agentId || '(not configured)'}</div>
                    <div>Identity Pool: {config.identityPoolId || '(not configured)'}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return <ChatInterface />;
    }
  };

  const getHeaderTitle = () => {
    const titles = {
      chat: 'Chat with SLyK',
      dashboard: 'Compliance Dashboard',
      assess: 'Run Assessment',
      harden: 'Harden Resources',
      remediate: 'Remediation Playbooks',
      reports: 'Generate Reports',
      history: 'Assessment History',
      settings: 'Settings',
    };
    return titles[activeView] || 'SLyK-53';
  };

  return (
    <div className="app">
      <Sidebar 
        activeView={activeView} 
        onViewChange={setActiveView}
        connectionStatus={connectionStatus}
      />
      <div className="main-content">
        <header className="header">
          <h2 className="header-title">{getHeaderTitle()}</h2>
          <div className="header-actions">
            <div className="header-status">
              <span className={`status-dot ${connectionStatus === 'connected' ? '' : 'disconnected'}`}></span>
              <span>{connectionStatus === 'connected' ? 'Agent Connected' : connectionStatus === 'demo' ? 'Demo Mode' : 'Connecting...'}</span>
            </div>
          </div>
        </header>
        {renderContent()}
      </div>
    </div>
  );
}

export default App;
