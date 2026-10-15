import React from 'react';

export default function ReminderBanner({ reminders, onMarkTaken, onOpenAssistant }) {
  if (!reminders || reminders.length === 0) return null;

  const activeReminder = reminders.find((r) => r.is_due_or_overdue) || reminders[0];

  return (
    <div
      style={{
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '12px',
        padding: '14px 18px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '20px' }}>🔔</span>
        <div>
          <div style={{ fontWeight: 600, fontSize: '14px', color: '#1e3a8a' }}>
            Medication Reminder: {activeReminder.name} ({activeReminder.dosage})
          </div>
          <div style={{ fontSize: '13px', color: '#1e40af' }}>
            Scheduled for {activeReminder.scheduled_time_12h} — {activeReminder.reminder_message}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          type="button"
          className="btn btn-taken"
          onClick={() => onMarkTaken(activeReminder.medication_id)}
        >
          ✓ Mark Taken
        </button>
        <button type="button" className="btn btn-outline" onClick={onOpenAssistant}>
          Open AI Follow-Up
        </button>
      </div>
    </div>
  );
}
