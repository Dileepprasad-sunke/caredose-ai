import React, { useState } from 'react';

export default function Medications({
  medications = [],
  onAddClick,
  onEditClick,
  onDeleteClick,
  onMarkStatus,
}) {
  const [selectedMed, setSelectedMed] = useState(null);

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Medications</h1>
          <p style={{ fontSize: '14px', color: '#64748b' }}>
            Manage your prescribed medication schedules, dosages, and active date ranges.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={onAddClick}>
          + Add Medication
        </button>
      </div>

      {medications.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: '#64748b', marginBottom: '12px' }}>
            Your medication list is currently empty.
          </p>
          <button type="button" className="btn btn-primary" onClick={onAddClick}>
            Add Your First Medication
          </button>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '16px',
          }}
        >
          {medications.map((med) => (
            <div key={med.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '8px' }}>
                  <div>
                    <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a' }}>
                      {med.name}
                    </h3>
                    <div style={{ fontSize: '13.5px', color: '#2563eb', fontWeight: 600 }}>
                      {med.dosage} &bull; {med.frequency}
                    </div>
                  </div>
                  <span className={`status-badge ${med.today_status || 'pending'}`}>
                    {med.today_status || 'pending'}
                  </span>
                </div>

                <div
                  style={{
                    marginTop: '12px',
                    padding: '10px 12px',
                    background: '#f8fafc',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#475569',
                    display: 'grid',
                    gap: '4px',
                  }}
                >
                  <div>
                    <strong>Scheduled Time:</strong> {med.time_12h || med.time}
                  </div>
                  <div>
                    <strong>Active Period:</strong> {med.start_date} to {med.end_date}
                  </div>
                  {med.instructions && (
                    <div>
                      <strong>Notes:</strong> {med.instructions}
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', paddingTop: '8px', borderTop: '1px solid #e2e8f0' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setSelectedMed(med)}
                >
                  View Details
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => onEditClick(med)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="btn btn-missed"
                  onClick={() => onDeleteClick(med.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Details Modal */}
      {selectedMed && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '16px',
            zIndex: 50,
          }}
        >
          <div className="card" style={{ maxWidth: '480px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>{selectedMed.name} — Details</h3>
              <button type="button" className="btn btn-outline" onClick={() => setSelectedMed(null)}>
                Close
              </button>
            </div>
            <div style={{ display: 'grid', gap: '8px', fontSize: '14px', color: '#334155' }}>
              <div><strong>Medicine Name:</strong> {selectedMed.name}</div>
              <div><strong>Dosage:</strong> {selectedMed.dosage}</div>
              <div><strong>Frequency:</strong> {selectedMed.frequency}</div>
              <div><strong>Scheduled Time:</strong> {selectedMed.time_12h || selectedMed.time}</div>
              <div><strong>Start Date:</strong> {selectedMed.start_date}</div>
              <div><strong>End Date:</strong> {selectedMed.end_date}</div>
              <div><strong>Today&apos;s Status:</strong> {selectedMed.today_status || 'pending'}</div>
              <div><strong>Instructions:</strong> {selectedMed.instructions || 'Standard schedule'}</div>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '18px' }}>
              <button
                type="button"
                className="btn btn-taken"
                onClick={() => {
                  onMarkStatus(selectedMed.id, 'taken');
                  setSelectedMed(null);
                }}
              >
                Mark Taken Today
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => {
                  const m = selectedMed;
                  setSelectedMed(null);
                  onEditClick(m);
                }}
              >
                Edit Medication
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
