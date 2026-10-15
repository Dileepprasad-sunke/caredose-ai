import React, { useState } from 'react';

export default function AuthScreen({ onLogin, onSignup, onDemoLogin, error, loading }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('demo@caredose.ai');
  const [password, setPassword] = useState('CareDose123!');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'login') {
      onLogin(email, password);
    } else {
      onSignup(name, email, password);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: '#f8fafc',
      }}
    >
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}
      >
        <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '32px' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div
              className="brand-logo"
              style={{ width: '48px', height: '48px', margin: '0 auto 12px', fontSize: '20px' }}
            >
              CD
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>CareDose AI</h1>
            <p style={{ fontSize: '14px', color: '#475569', marginTop: '4px' }}>
              Your Agentic AI Medication Adherence Companion
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              background: '#f1f5f9',
              padding: '4px',
              borderRadius: '8px',
              marginBottom: '20px',
            }}
          >
            <button
              type="button"
              className="btn"
              style={{
                background: mode === 'login' ? '#fff' : 'transparent',
                color: mode === 'login' ? '#0f172a' : '#64748b',
                boxShadow: mode === 'login' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
              }}
              onClick={() => setMode('login')}
            >
              Log In
            </button>
            <button
              type="button"
              className="btn"
              style={{
                background: mode === 'signup' ? '#fff' : 'transparent',
                color: mode === 'signup' ? '#0f172a' : '#64748b',
                boxShadow: mode === 'signup' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
              }}
              onClick={() => setMode('signup')}
            >
              Sign Up
            </button>
          </div>

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
            {mode === 'signup' && (
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Alex Rivera"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '11px', marginTop: '4px' }}
              disabled={loading}
            >
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In to CareDose AI' : 'Create Account'}
            </button>
          </form>

          <div
            style={{
              borderTop: '1px solid #e2e8f0',
              marginTop: '20px',
              paddingTop: '16px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
              College Project Demonstration Mode (Pre-loaded with sample data)
            </div>
            <button
              type="button"
              className="btn btn-outline"
              style={{ width: '100%' }}
              onClick={onDemoLogin}
              disabled={loading}
            >
              🚀 Launch with Demo Account (Alex Rivera)
            </button>
          </div>
        </div>
      </div>

      <footer className="safety-banner">
        CareDose AI is a medication adherence support tool. It does not provide medical diagnosis,
        prescriptions, dosage changes, or emergency medical advice.
      </footer>
    </div>
  );
}
