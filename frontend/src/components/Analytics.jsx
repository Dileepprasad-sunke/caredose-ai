import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function Analytics({ analytics }) {
  const weeklyChartRef = useRef(null);
  const weeklyChartInstance = useRef(null);

  useEffect(() => {
    if (!analytics || !analytics.weekly_chart || !weeklyChartRef.current) return;

    if (weeklyChartInstance.current) {
      weeklyChartInstance.current.destroy();
    }

    const ctx = weeklyChartRef.current.getContext('2d');
    const { labels, adherence_percentages, taken_counts, missed_counts } = analytics.weekly_chart;

    weeklyChartInstance.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Daily Adherence (%)',
            data: adherence_percentages,
            backgroundColor: '#2563eb',
            borderRadius: 6,
            yAxisID: 'y',
          },
          {
            label: 'Taken Doses',
            data: taken_counts,
            backgroundColor: '#10b981',
            borderRadius: 6,
            yAxisID: 'y1',
          },
          {
            label: 'Missed Doses',
            data: missed_counts,
            backgroundColor: '#ef4444',
            borderRadius: 6,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: { display: true, text: 'Adherence %' },
          },
          y1: {
            beginAtZero: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            title: { display: true, text: 'Dose Count' },
          },
        },
      },
    });

    return () => {
      if (weeklyChartInstance.current) {
        weeklyChartInstance.current.destroy();
      }
    };
  }, [analytics]);

  if (!analytics) {
    return <div className="card">Loading analytics...</div>;
  }

  const {
    overall = {},
    frequently_missed_time,
    patterns = [],
    period_breakdown = {},
    ai_adherence_insight,
  } = analytics;

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Adherence Analytics &amp; Patterns</h1>
        <p style={{ fontSize: '14px', color: '#64748b' }}>
          Real-time SQLite adherence calculations, 7-day Chart.js trends, and explainable pattern detection.
        </p>
      </div>

      {/* Overall Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #2563eb' }}>
          <div className="metric-label">Overall Adherence</div>
          <div className="metric-value" style={{ color: '#2563eb' }}>
            {overall.adherence_percentage ?? 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            {overall.taken_doses ?? 0} / {overall.total_scheduled ?? 0} total scheduled doses
          </div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="metric-label">Taken Doses (7-Day)</div>
          <div className="metric-value" style={{ color: '#047857' }}>
            {overall.taken_doses ?? 0}
          </div>
          <div style={{ fontSize: '12px', color: '#047857' }}>Confirmed on schedule</div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div className="metric-label">Missed Doses (7-Day)</div>
          <div className="metric-value" style={{ color: '#b91c1c' }}>
            {overall.missed_doses ?? 0}
          </div>
          <div style={{ fontSize: '12px', color: '#b91c1c' }}>
            Most missed time: <strong>{frequently_missed_time || 'None'}</strong>
          </div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #64748b' }}>
          <div className="metric-label">Pending Doses</div>
          <div className="metric-value" style={{ color: '#475569' }}>
            {overall.pending_doses ?? 0}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Awaiting confirmation</div>
        </div>
      </div>

      {/* Weekly Adherence Chart.js Canvas */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '12px' }}>
          Weekly Adherence Trend (Chart.js)
        </h2>
        <div style={{ height: '300px', position: 'relative' }}>
          <canvas ref={weeklyChartRef} />
        </div>
      </div>

      {/* Pattern Detection & Time-of-Day Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>
            Detected Adherence Patterns (Explainable AI)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {patterns.map((pt, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: pt.severity === 'warning' ? '#fffbeb' : '#f8fafc',
                  border: `1px solid ${pt.severity === 'warning' ? '#fde68a' : '#e2e8f0'}`,
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>{pt.title}</div>
                <div style={{ fontSize: '13.5px', color: '#334155', marginTop: '4px' }}>
                  {pt.description}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              marginTop: '16px',
              padding: '12px 14px',
              background: '#eff6ff',
              borderRadius: '10px',
              fontSize: '13.5px',
              color: '#1e3a8a',
            }}
          >
            <strong>AI-Generated Adherence Summary:</strong> {ai_adherence_insight}
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>
            Frequently Missed Time Windows
          </h3>
          <div style={{ fontSize: '13.5px', color: '#475569', marginBottom: '12px' }}>
            Most frequently missed scheduled time:{' '}
            <strong style={{ color: '#b91c1c' }}>{frequently_missed_time || 'None'}</strong>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {['morning', 'afternoon', 'evening'].map((period) => {
              const p = period_breakdown[period] || { taken: 0, missed: 0, total: 0, adherence_pct: 0 };
              return (
                <div
                  key={period}
                  style={{
                    padding: '12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, textTransform: 'capitalize' }}>
                    <span>{period} Window</span>
                    <span>{p.adherence_pct}% Adherence</span>
                  </div>
                  <div style={{ fontSize: '12.5px', color: '#64748b', marginTop: '4px' }}>
                    {p.taken} taken &bull; {p.missed} missed &bull; {p.total} total doses
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
