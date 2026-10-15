import React, { useState } from 'react';

export default function AIAssistant({
  aiState,
  onFollowUpChoice,
  onSendChat,
  onSimulateMissed,
}) {
  const [chatInput, setChatInput] = useState('');
  const [lastReply, setLastReply] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (!aiState) {
    return <div className="card">Loading Agentic AI Assistant...</div>;
  }

  const { active_follow_up, workflow, adherence_insight } = aiState;

  const handleOptionClick = async (choiceId) => {
    if (!active_follow_up) return;
    setSubmitting(true);
    try {
      const res = await onFollowUpChoice(
        active_follow_up.medication_id,
        choiceId,
        active_follow_up.scheduled_date
      );
      if (res && res.result) {
        setLastReply({
          type: choiceId,
          text: res.result.ai_reply,
          timestamp: res.result.timestamp,
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput('');
    setSubmitting(true);
    try {
      const res = await onSendChat(msg);
      if (res) {
        setLastReply({
          type: res.safety_triggered ? 'safety_boundary' : 'chat',
          text: res.reply,
          userQuestion: msg,
          timestamp: res.timestamp,
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>AI Assistant &amp; Follow-Up</h1>
          <p style={{ fontSize: '14px', color: '#64748b' }}>
            Agentic AI medication check-in powered by OBSERVE &rarr; REASON &rarr; PLAN &rarr; ACT &rarr; REMEMBER
          </p>
        </div>
        <button type="button" className="btn btn-outline" onClick={onSimulateMissed}>
          ⚡ Trigger Unconfirmed 2:00 PM Dose
        </button>
      </div>

      {/* Main Follow-Up Card (Matches Figma AI Follow-Up Specification) */}
      <div
        className="card"
        style={{
          borderLeft: '5px solid #2563eb',
          marginBottom: '20px',
          padding: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <span
            style={{
              background: '#eff6ff',
              color: '#2563eb',
              fontWeight: 700,
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '999px',
            }}
          >
            AGENTIC AI FOLLOW-UP
          </span>
          {active_follow_up && (
            <span style={{ fontSize: '12.5px', color: '#64748b' }}>
              Scheduled: {active_follow_up.scheduled_time_12h} &bull; {active_follow_up.medication_name} (
              {active_follow_up.dosage})
            </span>
          )}
        </div>

        {active_follow_up ? (
          <>
            <h2 style={{ fontSize: '19px', fontWeight: 700, color: '#0f172a', marginBottom: '16px' }}>
              &ldquo;{active_follow_up.prompt}&rdquo;
            </h2>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-taken"
                disabled={submitting}
                onClick={() => handleOptionClick('yes_taken')}
              >
                ✓ Yes, I took it
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={submitting}
                onClick={() => handleOptionClick('not_yet')}
              >
                ⏳ Not yet
              </button>
              <button
                type="button"
                className="btn btn-missed"
                disabled={submitting}
                onClick={() => handleOptionClick('not_sure')}
              >
                ❓ I&apos;m not sure
              </button>
            </div>
          </>
        ) : (
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#047857', marginBottom: '6px' }}>
              ✓ All due medications are currently confirmed!
            </h2>
            <p style={{ fontSize: '14px', color: '#475569' }}>
              {adherence_insight} (Click &ldquo;Trigger Unconfirmed 2:00 PM Dose&rdquo; above to demonstrate
              the AI follow-up prompt again.)
            </p>
          </div>
        )}

        {lastReply && (
          <div
            style={{
              marginTop: '18px',
              padding: '14px 16px',
              borderRadius: '10px',
              background:
                lastReply.type === 'yes_taken'
                  ? '#ecfdf5'
                  : lastReply.type === 'not_sure' || lastReply.type === 'safety_boundary'
                  ? '#fffbeb'
                  : '#f8fafc',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
              color: '#0f172a',
            }}
          >
            {lastReply.userQuestion && (
              <div style={{ fontSize: '12.5px', color: '#64748b', marginBottom: '4px' }}>
                <strong>You asked:</strong> &ldquo;{lastReply.userQuestion}&rdquo;
              </div>
            )}
            <strong>CareDose AI Response:</strong> {lastReply.text}
          </div>
        )}
      </div>

      {/* Two-Column Section: Agentic AI 5-Stage Pipeline + Safety-Guarded Chat */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '20px' }}>
        {/* Agentic Workflow Visualizer */}
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px' }}>
            Agentic AI Workflow Trace (OBSERVE &rarr; REASON &rarr; PLAN &rarr; ACT &rarr; REMEMBER)
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13.5px' }}>
            <div style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #2563eb' }}>
              <strong>1. OBSERVE:</strong> {workflow?.OBSERVE?.total_scheduled_today} scheduled today &bull;{' '}
              {workflow?.OBSERVE?.taken_today} taken &bull; {workflow?.OBSERVE?.pending_today} pending &bull;{' '}
              {workflow?.OBSERVE?.missed_today} missed ({workflow?.OBSERVE?.adherence_today_pct}% adherence).
            </div>

            <div style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #7c3aed' }}>
              <strong>2. REASON:</strong>{' '}
              {(workflow?.REASON || []).join(' ')}
            </div>

            <div style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #0ea5e9' }}>
              <strong>3. PLAN:</strong> {(workflow?.PLAN || []).join(' ')}
            </div>

            <div style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
              <strong>4. ACT:</strong> {workflow?.ACT?.adherence_insight}
            </div>

            <div style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #f59e0b' }}>
              <strong>5. REMEMBER:</strong> {workflow?.REMEMBER?.stored_events_count || 0} follow-up events
              persisted in SQLite database (`follow_up_events` table).
            </div>
          </div>
        </div>

        {/* Ask CareDose AI (Demonstrates Healthcare Safety Guardrails) */}
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>
            Ask CareDose AI (Safety Guardrails Active)
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px' }}>
            Ask about your schedule or test healthcare safety boundaries (e.g., asking to double a missed dose).
          </p>

          <form onSubmit={handleChatSubmit}>
            <div className="form-group">
              <input
                type="text"
                className="form-input"
                placeholder="e.g., I missed my dose, should I take a double dose?"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%' }}>
              Send Question
            </button>
          </form>

          <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>
              Quick Demo Prompts:
            </div>
            <button
              type="button"
              className="btn btn-outline"
              style={{ fontSize: '12px', justifyContent: 'flex-start' }}
              onClick={() => setChatInput('What is my adherence status and pattern this week?')}
            >
              &ldquo;What is my adherence status and pattern this week?&rdquo;
            </button>
            <button
              type="button"
              className="btn btn-outline"
              style={{ fontSize: '12px', justifyContent: 'flex-start' }}
              onClick={() => setChatInput('I missed my dose, what dose should I take or should I double my dose?')}
            >
              &ldquo;I missed my dose, should I double my dose?&rdquo; (Safety Test)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
