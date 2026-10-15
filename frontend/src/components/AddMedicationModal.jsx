import React, { useEffect, useState } from 'react';

export default function AddMedicationModal({ initialData, onSave, onCancel }) {
  const today = new Date().toISOString().split('T')[0];
  const nextMonth = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0];

  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('Once Daily');
  const [time, setTime] = useState('09:00');
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(nextMonth);
  const [instructions, setInstructions] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || '');
      setDosage(initialData.dosage || '');
      setFrequency(initialData.frequency || 'Once Daily');
      setTime(initialData.time || '09:00');
      setStartDate(initialData.start_date || today);
      setEndDate(initialData.end_date || nextMonth);
      setInstructions(initialData.instructions || '');
    } else {
      setName('');
      setDosage('');
      setFrequency('Once Daily');
      setTime('09:00');
      setStartDate(today);
      setEndDate(nextMonth);
      setInstructions('');
    }
  }, [initialData, today, nextMonth]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!name.trim() || !dosage.trim()) {
      setError('Please enter both the medicine name and dosage.');
      return;
    }
    if (endDate < startDate) {
      setError('End date cannot be earlier than start date.');
      return;
    }
    onSave({
      name: name.trim(),
      dosage: dosage.trim(),
      frequency,
      time,
      start_date: startDate,
      end_date: endDate,
      instructions: instructions.trim(),
    });
  };

  return (
    <div style={{ maxWidth: '640px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '6px' }}>
        {initialData ? 'Edit Medication' : 'Add Medication'}
      </h1>
      <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
        Configure your medication schedule, dosage, and reminder time.
      </p>

      <div className="card">
        {error && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '10px 12px',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '16px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Medicine Name *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Vitamin D, Metformin, Omega-3"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Dosage *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., 500 mg or 1 tablet"
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Frequency *</label>
              <select
                className="form-select"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
              >
                <option value="Once Daily">Once Daily</option>
                <option value="Twice Daily">Twice Daily</option>
                <option value="Three Times Daily">Three Times Daily</option>
                <option value="Every 8 Hours">Every 8 Hours</option>
                <option value="Weekly">Weekly</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Scheduled Time *</label>
              <input
                type="time"
                className="form-input"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Start Date *</label>
              <input
                type="date"
                className="form-input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">End Date *</label>
              <input
                type="date"
                className="form-input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Instructions / Notes (Optional)</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Take after food with a full glass of water"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
            <button type="submit" className="btn btn-primary">
              {initialData ? 'Save Changes' : 'Save Medication'}
            </button>
            <button type="button" className="btn btn-outline" onClick={onCancel}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
