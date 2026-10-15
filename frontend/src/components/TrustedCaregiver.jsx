import React, { useEffect, useState } from 'react';

export default function TrustedCaregiver({
  caregiverData,
  onSaveCaregiver,
  onDeleteCaregiver,
  onSimulateAlert,
}) {
  const existing = caregiverData?.caregiver;
  const simulatedAlerts = caregiverData?.simulated_alerts || [];

  const [name, setName] = useState('');
  const [contact, setContact] = useState('');
  const [relationship, setRelationship] = useState('Family Member');
  const [enabled, setEnabled] = useState(false);
  const [alertThreshold, setAlertThreshold] = useState(2);
  const [consentGiven, setConsentGiven] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (existing) {
      setName(existing.name || '');
      setContact(existing.contact || '');
      setRelationship(existing.relationship || 'Family Member');
      setEnabled(Boolean(existing.enabled));
      setAlertThreshold(existing.alert_threshold || 2);
      setConsentGiven(Boolean(existing.consent_given));
    }
  }, [existing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatusMsg('');
    setErrorMsg('');
    if (enabled && !consentGiven) {
      setErrorMsg('Please check the consent box to enable Trusted Caregiver alerts.');
      return;
    }
    try {
      await onSaveCaregiver({
        name,
        contact,
        relationship,
        enabled,
        alert_threshold: Number(alertThreshold),
        consent_given: consentGiven,
      });
      setStatusMsg('Trusted Caregiver configuration saved to SQLite.');
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleSimulate = async () => {
    setStatusMsg('');
    setErrorMsg('');
    try {
      const res = await onSimulateAlert();
      setStatusMsg(res.message || 'Caregiver notification triggered (Simulated MVP).');
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Trusted Caregiver Workflow</h1>
        <p style={{ fontSize: '14px', color: '#64748b' }}>
          Configure an optional caregiver contact with explicit user consent to receive alerts after
          repeated missed doses (Simulated in-app for MVP).
        </p>
      </div>

      {statusMsg && (
        <div
          style={{
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#047857',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '16px',
            fontWeight: 600,
            fontSize: '13.5px',
          }}
        >
          ✓ {statusMsg}
        </div>
      )}

      {errorMsg && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '16px',
            fontSize: '13.5px',
          }}
        >
          {errorMsg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        <div className="card">
          <h2 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '14px' }}>
            Caregiver Configuration
          </h2>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Caregiver Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Priya Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Caregiver Contact (Email / Phone) *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., priya@example.com | +91 98765 43210"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Relationship</label>
                <input
                  type="text"
                  className="form-input"
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Alert Threshold (Repeated Missed Doses)</label>
                <select
                  className="form-select"
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(Number(e.target.value))}
                >
                  <option value={1}>Notify after 1 missed dose</option>
                  <option value={2}>Notify after 2 repeated missed doses</option>
                  <option value={3}>Notify after 3 repeated missed doses</option>
                  <option value={4}>Notify after 4 repeated missed doses</option>
                </select>
              </div>
            </div>

            <div
              style={{
                padding: '12px 14px',
                background: '#f8fafc',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                marginBottom: '16px',
              }}
            >
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600, fontSize: '14px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                />
                Enable Trusted Caregiver Alerts
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  fontSize: '13px',
                  color: '#475569',
                  marginTop: '10px',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={consentGiven}
                  onChange={(e) => setConsentGiven(e.target.checked)}
                  style={{ marginTop: '3px' }}
                />
                <span>
                  <strong>Explicit User Consent:</strong> I consent to CareDose AI sharing missed-dose
                  threshold alerts with my designated caregiver above. I can revoke this consent at
                  any time.
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button type="submit" className="btn btn-primary">
                Save Caregiver Settings
              </button>
              <button type="button" className="btn btn-outline" onClick={handleSimulate}>
                🔔 Test Simulated Caregiver Notification
              </button>
              {existing && (
                <button
                  type="button"
                  className="btn btn-missed"
                  onClick={onDeleteCaregiver}
                >
                  Remove Caregiver
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Simulated Caregiver Notification Log */}
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>
            Simulated Caregiver Notification Log (MVP)
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '14px' }}>
            Per MVP rules, caregiver alerts are simulated inside the application when the missed-dose
            threshold is reached (no external SMS/WhatsApp is sent).
          </p>

          {simulatedAlerts.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '13.5px' }}>
              No caregiver alerts triggered yet. Click &ldquo;Test Simulated Caregiver Notification&rdquo;
              or mark doses as Missed to reach the threshold.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {simulatedAlerts.map((ev) => (
                <div
                  key={ev.id}
                  style={{
                    padding: '12px',
                    background: '#fffbeb',
                    border: '1px solid #fde68a',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#92400e',
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                    Caregiver Notification Triggered &bull; {ev.created_at}
                  </div>
                  <div>{ev.message}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
