import React from 'react';

const NAV_ITEMS = [
  { id: 'chat', icon: '💬', label: 'Chat', section: 'main' },
  { id: 'dashboard', icon: '📊', label: 'Dashboard', section: 'main' },
  { id: 'assess', icon: '🔍', label: 'Assess', section: 'actions' },
  { id: 'harden', icon: '🛡️', label: 'Harden', section: 'actions' },
  { id: 'remediate', icon: '🔧', label: 'Remediate', section: 'actions' },
  { id: 'reports', icon: '📄', label: 'Reports', section: 'documents' },
  { id: 'history', icon: '📜', label: 'History', section: 'documents' },
  { id: 'settings', icon: '⚙️', label: 'Settings', section: 'system' },
];

function Sidebar({ activeView, onViewChange, connectionStatus }) {
  const sections = {
    main: 'Main',
    actions: 'Actions',
    documents: 'Documents',
    system: 'System',
  };

  const groupedItems = NAV_ITEMS.reduce((acc, item) => {
    if (!acc[item.section]) acc[item.section] = [];
    acc[item.section].push(item);
    return acc;
  }, {});

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon">🛡️</div>
          <div className="logo-text">
            <h1>SLyK-53</h1>
            <span>Security Assistant</span>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {Object.entries(groupedItems).map(([section, items]) => (
          <div key={section} className="nav-section">
            <div className="nav-section-title">{sections[section]}</div>
            {items.map((item) => (
              <div
                key={item.id}
                className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                onClick={() => onViewChange(item.id)}
              >
                <span className="nav-item-icon">{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer" style={{ 
        padding: '16px 20px', 
        borderTop: '1px solid var(--border-color)',
        fontSize: '12px',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span className={`status-dot ${connectionStatus === 'connected' ? '' : 'disconnected'}`}></span>
          <span>{connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}</span>
        </div>
        <div>GRCP Platform v1.0</div>
        <div style={{ marginTop: '4px' }}>System 5065</div>
      </div>
    </div>
  );
}

export default Sidebar;
