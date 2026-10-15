import React, { useCallback, useEffect, useState } from 'react';
import { api, getToken, setToken } from './api.js';
import Sidebar from './components/Sidebar.jsx';
import SafetyBanner from './components/SafetyBanner.jsx';
import ReminderBanner from './components/ReminderBanner.jsx';
import AuthScreen from './components/AuthScreen.jsx';
import Dashboard from './components/Dashboard.jsx';
import Medications from './components/Medications.jsx';
import AddMedicationModal from './components/AddMedicationModal.jsx';
import AIAssistant from './components/AIAssistant.jsx';
import Analytics from './components/Analytics.jsx';
import TrustedCaregiver from './components/TrustedCaregiver.jsx';
import Settings from './components/Settings.jsx';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [editingMed, setEditingMed] = useState(null);

  const [dashboard, setDashboard] = useState(null);
  const [medications, setMedications] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [aiState, setAiState] = useState(null);
  const [caregiverData, setCaregiverData] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  const [reminders, setReminders] = useState([]);

  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState('');

  const refreshAllData = useCallback(async () => {
    if (!getToken()) return;
    try {
      const [dashRes, medsRes, anaRes, aiRes, cgRes, setRes, remRes] = await Promise.all([
        api.getDashboard(),
        api.getMedications(),
        api.getAnalytics(),
        api.getAIState(),
        api.getCaregiver(),
        api.getSettings(),
        api.getDueReminders(),
      ]);
      setDashboard(dashRes);
      setMedications(medsRes.medications || []);
      setAnalytics(anaRes);
      setAiState(aiRes);
      setCaregiverData(cgRes);
      setSettingsData(setRes);
      setReminders(remRes.reminders || []);
    } catch (err) {
      if (err.message.toLowerCase().includes('authentication') || err.message.toLowerCase().includes('token')) {
        setToken('');
        setUser(null);
      } else {
        setError(err.message);
      }
    }
  }, []);

  useEffect(() => {
    const token = getToken();
    if (token) {
      api
        .getMe()
        .then((res) => {
          setUser(res.user);
          refreshAllData();
        })
        .catch(() => {
          setToken('');
          setUser(null);
        });
    }
  }, [refreshAllData]);

  const handleLogin = async (email, password) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.login(email, password);
      setToken(res.token);
      setUser(res.user);
      await refreshAllData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (name, email, password) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.signup(name, email, password);
      setToken(res.token);
      setUser(res.user);
      await refreshAllData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    await handleLogin('demo@caredose.ai', 'CareDose123!');
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    }
    setToken('');
    setUser(null);
    setActiveTab('dashboard');
  };

  const handleMarkStatus = async (medId, status) => {
    setBusyId(medId);
    try {
      await api.markStatus(medId, status);
      await refreshAllData();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const handleSaveMedication = async (payload) => {
    try {
      if (editingMed) {
        await api.updateMedication(editingMed.id, payload);
      } else {
        await api.createMedication(payload);
      }
      setEditingMed(null);
      setActiveTab('medications');
      await refreshAllData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteMedication = async (medId) => {
    try {
      await api.deleteMedication(medId);
      await refreshAllData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleFollowUpChoice = async (medId, choice, scheduledDate) => {
    const res = await api.submitFollowUpResponse(medId, choice, scheduledDate);
    await refreshAllData();
    return res;
  };

  const handleAssistantChat = async (message) => {
    const res = await api.sendAssistantChat(message);
    await refreshAllData();
    return res;
  };

  const handleSimulateMissed = async () => {
    await api.simulateMissedDose();
    await refreshAllData();
    setActiveTab('ai-assistant');
  };

  if (!user) {
    return (
      <AuthScreen
        onLogin={handleLogin}
        onSignup={handleSignup}
        onDemoLogin={handleDemoLogin}
        error={error}
        loading={loading}
      />
    );
  }

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          if (tab !== 'add-medication') setEditingMed(null);
          setActiveTab(tab);
        }}
        user={user}
        onLogout={handleLogout}
        hasPendingFollowUp={Boolean(dashboard?.active_follow_up)}
      />

      <div className="main-area">
        <header className="topbar">
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#334155' }}>
            CareDose AI &bull; Agentic Medication Adherence System
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="status-badge taken">● SQLite Connected</span>
            <span style={{ fontSize: '13px', color: '#475569' }}>{user.name}</span>
          </div>
        </header>

        <main className="content-container" style={{ flex: 1 }}>
          {error && (
            <div
              style={{
                background: '#fef2f2',
                border: '1px solid #fecaca',
                color: '#b91c1c',
                padding: '10px 14px',
                borderRadius: '8px',
                marginBottom: '16px',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>{error}</span>
              <button
                type="button"
                onClick={() => setError('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 700 }}
              >
                ✕
              </button>
            </div>
          )}

          <ReminderBanner
            reminders={reminders}
            onMarkTaken={(id) => handleMarkStatus(id, 'taken')}
            onOpenAssistant={() => setActiveTab('ai-assistant')}
          />

          {activeTab === 'dashboard' && (
            <Dashboard
              dashboard={dashboard}
              onMarkStatus={handleMarkStatus}
              onOpenAddMedication={() => {
                setEditingMed(null);
                setActiveTab('add-medication');
              }}
              onOpenAssistant={() => setActiveTab('ai-assistant')}
              onSimulateMissed={handleSimulateMissed}
              busyId={busyId}
            />
          )}

          {activeTab === 'medications' && (
            <Medications
              medications={medications}
              onAddClick={() => {
                setEditingMed(null);
                setActiveTab('add-medication');
              }}
              onEditClick={(med) => {
                setEditingMed(med);
                setActiveTab('add-medication');
              }}
              onDeleteClick={handleDeleteMedication}
              onMarkStatus={handleMarkStatus}
            />
          )}

          {activeTab === 'add-medication' && (
            <AddMedicationModal
              initialData={editingMed}
              onSave={handleSaveMedication}
              onCancel={() => {
                setEditingMed(null);
                setActiveTab('medications');
              }}
            />
          )}

          {activeTab === 'ai-assistant' && (
            <AIAssistant
              aiState={aiState}
              onFollowUpChoice={handleFollowUpChoice}
              onSendChat={handleAssistantChat}
              onSimulateMissed={handleSimulateMissed}
            />
          )}

          {activeTab === 'analytics' && <Analytics analytics={analytics} />}

          {activeTab === 'caregiver' && (
            <TrustedCaregiver
              caregiverData={caregiverData}
              onSaveCaregiver={async (payload) => {
                await api.saveCaregiver(payload);
                await refreshAllData();
              }}
              onDeleteCaregiver={async () => {
                await api.deleteCaregiver();
                await refreshAllData();
              }}
              onSimulateAlert={async () => {
                const res = await api.simulateCaregiverAlert();
                await refreshAllData();
                return res;
              }}
            />
          )}

          {activeTab === 'settings' && (
            <Settings
              settingsData={settingsData}
              onSaveSettings={async (payload) => {
                await api.updateSettings(payload);
                await refreshAllData();
              }}
              onResetDemo={async () => {
                const res = await api.resetDemo();
                setToken(res.token);
                setUser(res.user);
                await refreshAllData();
              }}
            />
          )}
        </main>

        <SafetyBanner />
      </div>
    </div>
  );
}
