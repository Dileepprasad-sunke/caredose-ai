import React, { useEffect, useState } from 'react';

export default function Settings({ settingsData, onSaveSettings, onResetDemo }) {
  const [name, setName] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [followUpDelay, setFollowUpDelay] = useState(30);
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [savedBanner, setSavedBanner] = useState('');
  const [browserPerm, setBrowserPerm] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  );

  useEffect(() => {
    if (settingsData?.settings) {
      setName(settingsData.settings.name || '');
      setNotificationsEnabled(Boolean(settingsData.settings.notifications_enabled));
      setFollowUpDelay(settingsData.settings.follow_up_delay_minutes || 30);
      setTimezone(settingsData.settings.timezone || 'Asia/Kolkata');
    }
  }, [settingsData]);

  const requestBrowserNotifications = async () => {
    if (typeof Notification === 'undefined') {
      setBrowserPerm('unsupported');
      return;
    }
    const perm = await Notification.requestPermission();
    setBrowserPerm(perm);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSaveSettings({
      name,
      notifications_enabled: notificationsEnabled,
      follow_up_delay_minutes: Number(followUpDelay),
      timezone,
    });
    setSavedBanner('Account & reminder preferences saved.');
  };

  return (
    <div style={{ maxWidth: '680px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '6px' }}>Settings</h1>
      <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
        Manage your profile, reminder notifications, AI follow-up timing, and demonstration data.
      </p>

      {savedBanner && (
        <div
          style={{
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#047857',
            padding: '10px 14px',
            borderRadius: '8px',
            marginBottom: '16px',
            fontSize: '13.5px',
          }}
        >
          ✓ {savedBanner}
        </div>
      )}

      <div className="card" style={{ marginBottom: '20px' }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Account Name</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">AI Follow-Up Window (Minutes after due time)</label>
              <select
                className="form-select"
                value={followUpDelay}
                onChange={(e) => setFollowUpDelay(Number(e.target.value))}
              >
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={60}>60 minutes</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Timezone</label>
              <input
                type="text"
                className="form-input"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', fontWeight: 600 }}>
              <input
                type="checkbox"
                checked={notificationsEnabled}
                onChange={(e) => setNotificationsEnabled(e.target.checked)}
              />
              Enable In-App &amp; Browser Medication Reminders
            </label>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '16px' }}>
            <button type="button" className="btn btn-outline" onClick={requestBrowserNotifications}>
              Request Browser Notification Permission
            </button>
            <span style={{ fontSize: '12.5px', color: '#64748b' }}>
              Browser status: <strong>{browserPerm}</strong> (In-app banner active as fallback)
            </span>
          </div>

          <button type="submit" className="btn btn-primary">
            Save Settings
          </button>
        </form>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
          Demonstration Data Reset
        </h3>
        <p style={{ fontSize: '13.5px', color: '#475569', marginBottom: '12px' }}>
          Restore the default college demonstration state (Vitamin D at 9:00 AM, Medicine B at 2:00 PM,
          Medicine C at 8:00 PM, and 7-day analytics history).
        </p>
        <button type="button" className="btn btn-outline" onClick={onResetDemo}>
          🔄 Reset Demo Data to Default State
        </button>
      </div>
    </div>
  );
}
