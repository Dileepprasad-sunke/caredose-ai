# CareDose AI — 17-Step College Demonstration Guide (`docs/DEMO_WALKTHROUGH.md`)

Use this step-by-step script during your viva or project presentation to demonstrate every core feature of CareDose AI without any manual database edits.

1. **Login**: Open the CareDose AI login screen and sign in using the demo account (`demo@caredose.ai` / `CareDose123!`) or click **Launch with Demo Account**.
2. **Open Dashboard**: Point out the personalized greeting, the 4 real-time adherence metric cards (`Today's Adherence %`, `Taken Count`, `Missed Count`, `Pending Count`), and the **AI Adherence Insight** card.
3. **Show Today's Medications**: Highlight the pre-seeded demonstration schedule:
   - **Vitamin D** (`500 mg`, `9:00 AM`) — *Taken*
   - **Medicine B** (`1 tablet`, `2:00 PM`) — *Pending*
   - **Medicine C** (`1 tablet`, `8:00 PM`) — *Pending*
4. **Add a Medication**: Click **+ Add Medication**, enter `Omega-3` (`1000 mg`, `Once Daily`, `12:30 PM`, start/end dates), and click **Save Medication**.
5. **Mark One Medication as Taken**: Return to the **Dashboard** and click **Mark Taken** on `Omega-3` (or `Medicine C`).
6. **Show Adherence Percentage Changing**: Point out how `Today's Adherence %` and `Taken Count` immediately recalculate (`Taken scheduled doses / Total scheduled doses × 100`).
7. **Simulate a Missed / Unconfirmed Medication**: Click **Simulate Unconfirmed Dose** on the Dashboard (or mark a dose as `Missed`).
8. **Open AI Assistant**: Click **AI Assistant** in the left navigation bar.
9. **Show AI Follow-Up**: Point out the active follow-up card: *"Your 2:00 PM medication (Medicine B — 1 tablet) has not been confirmed. Did you take it?"* with the three buttons (`Yes, I took it`, `Not yet`, `I'm not sure`).
10. **Confirm the Medication**: Click **Yes, I took it**.
11. **Show Database / Status Update**: Show the confirmation message from CareDose AI and return to the Dashboard to verify `Medicine B` is now **Taken** (green badge) and persisted in SQLite.
12. **Open Analytics**: Click **Analytics** in the sidebar.
13. **Show Weekly Adherence**: Highlight the 7-day **Chart.js** bar chart comparing daily adherence percentages, taken doses, and missed doses.
14. **Show an Adherence Pattern**: Point out the **Detected Adherence Patterns** card showing: *"You frequently miss medications scheduled in the afternoon (2:00 PM)."*
15. **Open Trusted Caregiver**: Click **Trusted Caregiver** in the sidebar.
16. **Demonstrate the Optional Caregiver Workflow**: Show the caregiver fields (`Priya Sharma`, contact, threshold = `2 repeated missed doses`, explicit user consent checkbox) and click **Test Simulated Caregiver Notification** to display the in-app simulated alert banner and log entry.
17. **Show the Agentic AI Workflow (`OBSERVE → REASON → PLAN → ACT → REMEMBER`)**: Open **AI Assistant** and walk the evaluator through the 5-stage live trace panel and test the medical safety guardrail by asking *"I missed my dose, should I double my dose?"*.
