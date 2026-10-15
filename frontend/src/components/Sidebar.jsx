import React from 'react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'medications', label: 'Medications', icon: '💊' },
  { id: 'add-medication', label: 'Add Medication', icon: '➕' },
  { id: 'ai-assistant', label: 'AI Assistant', icon: '🤖' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
  { id: 'caregiver', label: 'Trusted Caregiver', icon: '🤝' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar({ activeTab, onSelectTab, user, onLogout, hasPendingFollowUp }) {
  return (
    <aside className="sidebar" aria-label="Main Navigation">
      <div>
        <div className="brand-header">
          <div className="brand-logo">CD</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px', color: '#0f172a' }}>CareDose AI</div>
            <div style={{ fontSize: '11.5px', color: '#64748b' }}>Adherence Companion</div>
          </div>
        </div>

        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={`nav-btn ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => onSelectTab(item.id)}
              >
                <span>{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.id === 'ai-assistant' && hasPendingFollowUp && (
                  <span
                    style={{
                      background: '#ef4444',
                      color: '#fff',
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '999px',
                    }}
                  >
                    1
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginTop: '16px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '2px' }}>
          {user?.name}
        </div>
        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
          {user?.email}
        </div>
        <button type="button" className="btn btn-outline" style={{ width: '100%' }} onClick={onLogout}>
          Log Out
        </button>
      </div>
    </aside>
  );
}
