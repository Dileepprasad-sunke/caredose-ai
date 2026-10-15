# CareDose AI — Agentic AI Medication Adherence Companion

**CareDose AI** is an end-to-end college AI/ML MVP web application designed to help individuals stay on top of their daily medication schedules through deterministic schedule tracking, explainable adherence analytics, an **Agentic AI (`Observe → Reason → Plan → Act → Remember`)** follow-up workflow, and an optional consent-based **Trusted Caregiver** simulation.

---

## 1. Problem

Missing or delaying scheduled medications is a widespread challenge for patients managing daily regimens. Busy afternoon routines, forgetfulness, and lack of timely follow-up often lead to unconfirmed or missed doses. Traditional alarm apps simply ring once and disappear—they do not check back when a dose remains unconfirmed, nor do they identify recurring adherence patterns (such as consistently missing afternoon doses) or offer an optional safety net with a family caregiver.

---

## 2. Solution

**CareDose AI** acts as an intelligent, safety-first medication adherence companion:
- **Structured Daily Schedule**: Displays a clear daily view of every medication, dosage, scheduled time, and real-time status (`Taken`, `Missed`, `Pending`).
- **Proactive Agentic Follow-Up**: When a scheduled dose remains unconfirmed (`Pending`), the Agentic AI prompts the user with clear options (`Yes, I took it`, `Not yet`, `I'm not sure`) and updates the database and adherence percentage immediately upon confirmation.
- **Explainable Pattern Detection**: Identifies simple, non-clinical patterns from real SQLite logs (for example, *"You frequently miss medications scheduled in the afternoon (2:00 PM)"*).
- **Consent-Driven Caregiver Support**: Allows users to configure a trusted caregiver and a missed-dose threshold (e.g., notify after 2 repeated missed doses), with in-app simulated notifications for MVP demonstration.

---

## 3. Features

- **Medication Scheduling (Full CRUD)**: Add, view details, edit, and delete medications with name, dosage, frequency, scheduled time, start date, and end date.
- **Reminders**: Browser notification support with an automatic in-app reminder banner fallback and one-click `Mark Taken`.
- **Taken / Missed / Pending Tracking**: Instant status updates stored persistently in SQLite with duplicate-log prevention (`UNIQUE(medication_id, scheduled_date, scheduled_time)`).
- **Adherence Analytics**: Real-time calculation (`Taken scheduled doses / Total scheduled doses × 100`) and a responsive 7-day **Chart.js** adherence chart.
- **Agentic AI Follow-Up**: Interactive confirmation flow for unconfirmed doses (`Yes, I took it`, `Not yet`, `I'm not sure`) plus live visualization of the 5-stage agent loop.
- **Pattern Detection**: Automatically highlights frequently missed time windows (morning/afternoon/evening), repeatedly missed medications, lower-adherence days, and weekly trends.
- **Trusted Caregiver Support**: Add/edit/remove a caregiver, require explicit user consent, configure an alert threshold, and trigger simulated MVP caregiver notifications.

---

## 4. Agentic AI (`Observe → Reason → Plan → Act → Remember`)

CareDose AI implements a transparent, 5-stage agent loop in `ai-agent/agent.py`:

1. **OBSERVE**: Reads the user's active medication schedule, today's `pending`/`taken`/`missed` logs, 7-day adherence history, caregiver preferences, and past follow-up events from SQLite.
2. **REASON**: Uses deterministic Python rules to identify overdue unconfirmed (`pending`) doses, count repeated `missed` doses against the caregiver threshold, and compute adherence patterns across time windows.
3. **PLAN**: Selects safe, bounded actions—queueing an interactive follow-up check-in, preparing an adherence pattern insight, or triggering a simulated caregiver alert if enabled with consent.
4. **ACT**: Displays the follow-up prompt in the AI Assistant, processes user confirmations (`Yes, I took it` updates SQLite and recalculates adherence), generates friendly adherence insights, and triggers simulated caregiver alerts.
5. **REMEMBER**: Persists every follow-up prompt, user response, and caregiver simulation event into the `follow_up_events` and `medication_logs` SQLite tables.

---

## 5. Technology Stack

- **Frontend**: React 18, Vite, CSS (Healthcare SaaS Design System), Chart.js
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic
- **Database**: Persistent SQLite (`caredose.db`)
- **AI**: Deterministic Python rule engine (`ai-agent/`) + optional LLM API (`GEMINI_API_KEY` or `OPENAI_API_KEY`) for natural-language phrasing with safe offline fallback

---

## 6. Architecture

```text
React Frontend (Dashboard, Medications, AI Assistant, Analytics, Caregiver, Settings)
       │
       ▼  REST JSON API (/api/*)
FastAPI Backend (Authentication, CRUD, Adherence Math, Reminder Engine)
       │
       ├──────────────────────────────┐
       ▼                              ▼
SQLite Database (`database/`)    Agentic AI (`ai-agent/`)
- users                          - Observe → Reason → Plan → Act → Remember
- medications                    - Explainable Pattern Detection (`patterns.py`)
- medication_logs                - Medical Safety Guardrails (`safety.py`)
- caregivers                     - LLM Client + Safe Fallback (`llm_client.py`)
- follow_up_events
```

---

## 7. Safety & Healthcare Limitations

> **Safety Notice:** *"CareDose AI is a medication adherence support tool. It does not provide medical diagnosis, prescriptions, dosage changes, or emergency medical advice."*

- **Deterministic Critical Logic**: The LLM never controls medication schedules, pending/missed status transitions, adherence math, caregiver thresholds, or database writes.
- **Strict Medical Boundaries (`ai-agent/safety.py`)**: CareDose AI never diagnoses conditions, prescribes medications, alters dosages, or recommends doubling a missed dose. When a user selects *"I'm not sure"* or asks what dose to take after missing a medication, the assistant instructs them to check their prescription instructions or contact a pharmacist or healthcare professional.

---

## 8. Installation & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Step 1: Clone & Configure Environment
```bash
cd CareDose-AI
cp .env.example .env
```

### Step 2: Start the FastAPI Backend & SQLite Database
```bash
pip install -r backend/requirements.txt
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
*On first launch, `database/seed.py` automatically creates `database/caredose.db` and seeds the demonstration account (`demo@caredose.ai` / `CareDose123!`).*

### Step 3: Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Deploying on Replit
Import the repository into Replit and click **Run**. Replit uses `.replit` and `run_replit.sh` to install dependencies, build the React frontend, and serve both the API and web app on port `8000`.

---

## 9. Future Improvements

- **Real Multi-Channel Notifications**: Optional push notifications, SMS, or WhatsApp integration via verified healthcare messaging gateways.
- **Advanced Personalization**: Adaptive reminder lead times based on routine habits.
- **Healthcare Provider Integrations**: FHIR-compatible export for sharing adherence summaries with clinicians or pharmacists.
- **Stronger Security**: OAuth2 / multi-factor authentication and encrypted-at-rest database storage.
- **Advanced Analytics**: Monthly adherence heatmaps and multi-medication refill tracking.
