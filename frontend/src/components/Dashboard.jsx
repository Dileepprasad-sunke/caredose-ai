import React from 'react';

export default function Dashboard({
  dashboard,
  onMarkStatus,
  onOpenAddMedication,
  onOpenAssistant,
  onSimulateMissed,
  busyId,
}) {
  if (!dashboard) {
    return <div className="card">Loading dashboard...</div>;
  }

  const {
    greeting,
    date,
    adherence_percentage,
    taken_count,
    missed_count,
    pending_count,
    today_schedule = [],
    ai_insight,
    active_follow_up,
    caregiver_simulation,
  } = dashboard;

  return (
    <div>
      {/* Header Row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '24px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>{greeting}</h1>
          <p style={{ fontSize: '14px', color: '#64748b' }}>
            Today&apos;s Medication Schedule &bull; {date} &bull;{' '}
            <span style={{ color: '#2563eb', fontWeight: 600 }}>Demo Data Active</span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-outline" onClick={onSimulateMissed}>
            ⚡ Simulate Unconfirmed Dose
          </button>
          <button type="button" className="btn btn-primary" onClick={onOpenAddMedication}>
            + Add Medication
          </button>
        </div>
      </div>

      {/* Simulated Caregiver Alert Banner if threshold reached */}
      {caregiver_simulation && caregiver_simulation.triggered && (
        <div
          style={{
            background: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '12px',
            padding: '14px 18px',
            marginBottom: '20px',
            color: '#92400e',
            fontSize: '13.5px',
          }}
        >
          <strong>🤝 Trusted Caregiver Workflow (Simulated MVP):</strong>{' '}
          {caregiver_simulation.banner_message}
        </div>
      )}

      {/* 4 Summary Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #2563eb' }}>
          <div className="metric-label">Today&apos;s Adherence</div>
          <div className="metric-value" style={{ color: '#2563eb' }}>
            {adherence_percentage}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
            {taken_count} of {today_schedule.length} scheduled doses taken
          </div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">Taken Count</div>
          <div className="metric-value" style={{ color: '#047857' }}>
            {taken_count}
          </div>
          <div style={{ fontSize: '12px', color: '#047857', marginTop: '4px' }}>Completed today</div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">Missed Count</div>
          <div className="metric-value" style={{ color: '#b91c1c' }}>
            {missed_count}
          </div>
          <div style={{ fontSize: '12px', color: '#b91c1c', marginTop: '4px' }}>Needs attention</div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #64748b' }}>
          <div className="metric-label">Pending Count</div>
          <div className="metric-value" style={{ color: '#475569' }}>
            {pending_count}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Awaiting confirmation</div>
        </div>
      </div>

      {/* Main Two-Column Grid: Today's Schedule + AI Insight Card */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.65fr 1fr',
          gap: '20px',
          alignItems: 'start',
        }}
      >
        {/* Today's Medication Schedule */}
        <div className="card">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <h2 style={{ fontSize: '17px', fontWeight: 700 }}>Today&apos;s Medication Schedule</h2>
            <span style={{ fontSize: '12.5px', color: '#64748b' }}>
              {today_schedule.length} scheduled
            </span>
          </div>

          {today_schedule.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
              No medications scheduled for today. Click &ldquo;+ Add Medication&rdquo; to begin.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {today_schedule.map((med) => (
                <div
                  key={med.medication_id}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '14px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                    background:
                      med.status === 'taken'
                        ? '#f8fafc'
                        : med.status === 'missed'
                        ? '#fffcfc'
                        : '#ffffff',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '15px', color: '#0f172a' }}>
                        {med.name}
                      </span>
                      <span className={`status-badge ${med.status}`}>{med.status}</span>
                      {med.is_demo && (
                        <span
                          style={{
                            fontSize: '11px',
                            background: '#f1f5f9',
                            color: '#64748b',
                            padding: '2px 6px',
                            borderRadius: '4px',
                          }}
                        >
                          Demo
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '13px', color: '#475569', marginTop: '4px' }}>
                      Dosage: <strong>{med.dosage}</strong> &bull; Scheduled:{' '}
                      <strong>{med.time_12h}</strong> ({med.frequency})
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="btn btn-taken"
                      disabled={busyId === med.medication_id || med.status === 'taken'}
                      onClick={() => onMarkStatus(med.medication_id, 'taken')}
                    >
                      {med.status === 'taken' ? '✓ Taken' : 'Mark Taken'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-missed"
                      disabled={busyId === med.medication_id || med.status === 'missed'}
                      onClick={() => onMarkStatus(med.medication_id, 'missed')}
                    >
                      {med.status === 'missed' ? '✕ Missed' : 'Mark Missed'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI Insight Card + Quick Follow-Up Preview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            className="card"
            style={{
              background: 'linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)',
              borderColor: '#bfdbfe',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <span style={{ fontSize: '18px' }}>🤖</span>
              <h3 style={{ fontSize: '15.5px', fontWeight: 700, color: '#1e3a8a' }}>
                AI Adherence Insight
              </h3>
            </div>
            <p style={{ fontSize: '13.5px', color: '#1e293b', lineHeight: 1.6 }}>{ai_insight}</p>

            {active_follow_up && (
              <div
                style={{
                  marginTop: '14px',
                  paddingTop: '14px',
                  borderTop: '1px solid #dbeafe',
                }}
              >
                <div
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: '#b45309',
                    textTransform: 'uppercase',
                    marginBottom: '6px',
                  }}
                >
                  Action Needed &bull; Unconfirmed Dose
                </div>
                <p style={{ fontSize: '13.5px', fontWeight: 600, color: '#0f172a', marginBottom: '10px' }}>
                  &ldquo;{active_follow_up.prompt}&rdquo;
                </p>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  onClick={onOpenAssistant}
                >
                  Respond in AI Assistant &rarr;
                </button>
              </div>
            )}
          </div>

          <div className="card">
            <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px' }}>
              Agentic AI Loop Status
            </h4>
            <div style={{ fontSize: '12.5px', color: '#475569', display: 'grid', gap: '6px' }}>
              <div>
                <strong>1. OBSERVE:</strong> Monitoring {today_schedule.length} scheduled doses today
              </div>
              <div>
                <strong>2. REASON:</strong> {pending_count} pending, {missed_count} missed
              </div>
              <div>
                <strong>3. PLAN:</strong>{' '}
                {active_follow_up ? 'Follow-up prompt queued' : 'Routine schedule monitoring'}
              </div>
              <div>
                <strong>4. ACT:</strong> Interactive confirmation &amp; insight active
              </div>
              <div>
                <strong>5. REMEMBER:</strong> Persistent SQLite log tracking enabled
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
