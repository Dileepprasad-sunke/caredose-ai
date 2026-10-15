"""
CareDose AI — FastAPI Backend Entry Point (backend/main.py)
Provides REST API endpoints for:
- Authentication (Signup, Login, Logout, Current User, Demo Account Reset)
- Dashboard (Greeting, Today's Adherence, Today's Schedule, AI Insight Card)
- Medications CRUD (Create, Read, Update, Delete)
- Medication Status Tracking (Mark Taken / Mark Missed / Pending with duplicate prevention)
- Analytics (Overall Adherence, Weekly Chart.js data, Frequently Missed Times, Patterns)
- Reminder System (Due/Overdue medication check)
- Agentic AI Workflow (OBSERVE -> REASON -> PLAN -> ACT -> REMEMBER, Follow-Up, Safety Chat)
- Trusted Caregiver Workflow (Add/Edit/Remove, Consent, Threshold Simulation)
- Settings (Profile, Notification & Follow-up preferences)
"""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db import get_connection, init_db
from database.seed import hash_password, seed_demo_data, verify_password
from backend.auth import create_access_token, get_current_user
from backend.adherence import compute_adherence_metrics, get_weekly_adherence_series
from backend.schemas import (
    AssistantChatRequest,
    CaregiverUpdateRequest,
    FollowUpResponseRequest,
    LoginRequest,
    MedicationCreateRequest,
    MedicationUpdateRequest,
    SettingsUpdateRequest,
    SignupRequest,
    StatusUpdateRequest,
)

# Dynamically load the `ai-agent` package (since directory name has a hyphen per project spec)
AI_AGENT_DIR = ROOT_DIR / "ai-agent"
spec = importlib.util.spec_from_file_location(
    "ai_agent",
    str(AI_AGENT_DIR / "__init__.py"),
    submodule_search_locations=[str(AI_AGENT_DIR)],
)
ai_agent = importlib.util.module_from_spec(spec)
sys.modules["ai_agent"] = ai_agent
spec.loader.exec_module(ai_agent)

run_agent_cycle = ai_agent.run_agent_cycle
handle_followup_response = ai_agent.handle_followup_response
handle_assistant_chat = ai_agent.handle_assistant_chat
detect_adherence_patterns = ai_agent.detect_adherence_patterns
format_time_12h = ai_agent.format_time_12h
SAFETY_NOTICE = ai_agent.SAFETY_NOTICE

app = FastAPI(
    title="CareDose AI API",
    description="Agentic AI-Powered Medication Adherence Companion MVP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize SQLite schema and ensure demo data exists on first launch."""
    init_db()
    seed_demo_data(force_reset=False)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "CareDose AI Backend",
        "safety_notice": SAFETY_NOTICE,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# 1. AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest):
    email_clean = req.email.strip().lower()
    if "@" not in email_clean or "." not in email_clean.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email_clean,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please log in instead.",
            )

        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pw_hash = hash_password(req.password)
        cur = conn.execute(
            """
            INSERT INTO users (name, email, password, notifications_enabled, follow_up_delay_minutes, timezone, created_at)
            VALUES (?, ?, ?, 1, 30, 'Asia/Kolkata', ?)
            """,
            (req.name.strip(), email_clean, pw_hash, now_iso),
        )
        user_id = cur.lastrowid
        conn.commit()

        token = create_access_token(user_id=user_id, email=email_clean)
        return {
            "token": token,
            "user": {
                "id": user_id,
                "name": req.name.strip(),
                "email": email_clean,
                "notifications_enabled": True,
                "follow_up_delay_minutes": 30,
                "timezone": "Asia/Kolkata",
            },
        }
    finally:
        conn.close()


@app.post("/api/auth/login")
def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email_clean,)).fetchone()
        if not row or not verify_password(req.password, row["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Try demo@caredose.ai / CareDose123! for the demo account.",
            )
        user = dict(row)
        token = create_access_token(user_id=user["id"], email=user["email"])
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "notifications_enabled": bool(user["notifications_enabled"]),
                "follow_up_delay_minutes": user["follow_up_delay_minutes"],
                "timezone": user["timezone"],
            },
        }
    finally:
        conn.close()


@app.post("/api/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully.", "user_id": current_user["id"]}


@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}


@app.post("/api/auth/demo-reset")
def reset_demo_account():
    """Reset the demo account back to clean initial state for live demonstrations."""
    res = seed_demo_data(force_reset=True)
    conn = get_connection()
    try:
        user = dict(conn.execute("SELECT * FROM users WHERE email = 'demo@caredose.ai'").fetchone())
        token = create_access_token(user_id=user["id"], email=user["email"])
        return {
            "message": res["message"],
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "notifications_enabled": bool(user["notifications_enabled"]),
                "follow_up_delay_minutes": user["follow_up_delay_minutes"],
                "timezone": user["timezone"],
            },
        }
    finally:
        conn.close()


# ============================================================================
# 2. DASHBOARD ENDPOINT
# ============================================================================

@app.get("/api/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()

    # Run Agentic AI cycle so today's logs are initialized and insights are fresh
    agent_data = run_agent_cycle(user_id)

    conn = get_connection()
    try:
        schedule_rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT
                    m.id AS medication_id,
                    m.name,
                    m.dosage,
                    m.frequency,
                    m.time,
                    m.start_date,
                    m.end_date,
                    m.instructions,
                    m.is_demo,
                    COALESCE(ml.status, 'pending') AS status,
                    ml.timestamp AS status_timestamp,
                    ml.id AS log_id
                FROM medications m
                LEFT JOIN medication_logs ml
                    ON ml.medication_id = m.id AND ml.scheduled_date = ?
                WHERE m.user_id = ? AND m.start_date <= ? AND m.end_date >= ?
                ORDER BY m.time ASC
                """,
                (today_str, user_id, today_str, today_str),
            ).fetchall()
        ]

        for item in schedule_rows:
            item["time_12h"] = format_time_12h(item["time"])
            item["is_demo"] = bool(item["is_demo"])

        metrics = compute_adherence_metrics(schedule_rows)
        hour = datetime.now().hour
        greeting_prefix = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

        return {
            "greeting": f"{greeting_prefix}, {current_user['name']}",
            "date": today_str,
            "adherence_percentage": metrics["adherence_percentage"],
            "taken_count": metrics["taken_doses"],
            "missed_count": metrics["missed_doses"],
            "pending_count": metrics["pending_doses"],
            "total_scheduled": metrics["total_scheduled"],
            "today_schedule": schedule_rows,
            "ai_insight": agent_data["adherence_insight"],
            "active_follow_up": agent_data["active_follow_up"],
            "caregiver_simulation": agent_data["caregiver_simulation"],
            "agent_workflow": agent_data["workflow"],
            "safety_notice": SAFETY_NOTICE,
        }
    finally:
        conn.close()


# ============================================================================
# 3. MEDICATION CRUD & STATUS TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/medications")
def list_medications(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    conn = get_connection()
    try:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT
                    m.*,
                    COALESCE(ml.status, 'pending') AS today_status,
                    ml.timestamp AS today_status_timestamp
                FROM medications m
                LEFT JOIN medication_logs ml
                    ON ml.medication_id = m.id AND ml.scheduled_date = ?
                WHERE m.user_id = ?
                ORDER BY m.time ASC
                """,
                (today_str, user_id),
            ).fetchall()
        ]
        for r in rows:
            r["time_12h"] = format_time_12h(r["time"])
            r["is_demo"] = bool(r["is_demo"])
        return {"medications": rows}
    finally:
        conn.close()


@app.get("/api/medications/{med_id}")
def get_medication_detail(med_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    try:
        med_row = conn.execute(
            "SELECT * FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id)
        ).fetchone()
        if not med_row:
            raise HTTPException(status_code=404, detail="Medication not found.")
        med = dict(med_row)
        med["time_12h"] = format_time_12h(med["time"])
        med["is_demo"] = bool(med["is_demo"])

        logs = [
            dict(r)
            for r in conn.execute(
                """
                SELECT * FROM medication_logs
                WHERE medication_id = ? AND user_id = ?
                ORDER BY scheduled_date DESC, scheduled_time DESC
                LIMIT 14
                """,
                (med_id, user_id),
            ).fetchall()
        ]
        metrics = compute_adherence_metrics(logs)
        return {"medication": med, "recent_logs": logs, "adherence": metrics}
    finally:
        conn.close()


@app.post("/api/medications", status_code=status.HTTP_201_CREATED)
def create_medication(req: MedicationCreateRequest, current_user: dict = Depends(get_current_user)):
    if req.end_date < req.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO medications (user_id, name, dosage, frequency, time, start_date, end_date, instructions, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                user_id,
                req.name.strip(),
                req.dosage.strip(),
                req.frequency.strip(),
                req.time.strip(),
                req.start_date,
                req.end_date,
                (req.instructions or "").strip(),
                now_str,
            ),
        )
        med_id = cur.lastrowid

        # If today is within [start_date, end_date], create today's pending schedule log
        if req.start_date <= today_str <= req.end_date:
            conn.execute(
                """
                INSERT OR IGNORE INTO medication_logs
                (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (user_id, med_id, today_str, req.time.strip(), now_str),
            )
        conn.commit()

        created = dict(
            conn.execute("SELECT * FROM medications WHERE id = ?", (med_id,)).fetchone()
        )
        created["time_12h"] = format_time_12h(created["time"])
        created["today_status"] = "pending"
        return {"medication": created, "message": f"{created['name']} added to your schedule."}
    finally:
        conn.close()


@app.put("/api/medications/{med_id}")
def update_medication(
    med_id: int, req: MedicationUpdateRequest, current_user: dict = Depends(get_current_user)
):
    if req.end_date < req.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Medication not found.")

        conn.execute(
            """
            UPDATE medications
            SET name = ?, dosage = ?, frequency = ?, time = ?, start_date = ?, end_date = ?, instructions = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                req.name.strip(),
                req.dosage.strip(),
                req.frequency.strip(),
                req.time.strip(),
                req.start_date,
                req.end_date,
                (req.instructions or "").strip(),
                med_id,
                user_id,
            ),
        )

        # Keep today's scheduled_time synchronized
        conn.execute(
            """
            UPDATE medication_logs
            SET scheduled_time = ?, timestamp = ?
            WHERE medication_id = ? AND user_id = ? AND scheduled_date = ?
            """,
            (req.time.strip(), now_str, med_id, user_id, today_str),
        )
        conn.commit()

        updated = dict(conn.execute("SELECT * FROM medications WHERE id = ?", (med_id,)).fetchone())
        updated["time_12h"] = format_time_12h(updated["time"])
        return {"medication": updated, "message": f"{updated['name']} updated successfully."}
    finally:
        conn.close()


@app.delete("/api/medications/{med_id}")
def delete_medication(med_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Medication not found.")

        conn.execute("DELETE FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id))
        conn.commit()
        return {"message": f"{existing['name']} deleted from your schedule.", "deleted_id": med_id}
    finally:
        conn.close()


@app.post("/api/medications/{med_id}/status")
def mark_medication_status(
    med_id: int, req: StatusUpdateRequest, current_user: dict = Depends(get_current_user)
):
    """
    Mark a scheduled medication as 'taken', 'missed', or 'pending'.
    Prevents duplicate logs via UNIQUE(medication_id, scheduled_date, scheduled_time) upsert.
    Automatically checks Trusted Caregiver threshold when marked 'missed'.
    """
    user_id = current_user["id"]
    target_date = req.scheduled_date or datetime.now().date().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        med = conn.execute(
            "SELECT * FROM medications WHERE id = ? AND user_id = ?", (med_id, user_id)
        ).fetchone()
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found.")

        conn.execute(
            """
            INSERT INTO medication_logs (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(medication_id, scheduled_date, scheduled_time)
            DO UPDATE SET status = excluded.status, timestamp = excluded.timestamp
            """,
            (user_id, med_id, target_date, med["time"], req.status, now_str),
        )

        # If marked 'taken', resolve any open follow-up prompt for this medication today
        if req.status == "taken":
            conn.execute(
                """
                UPDATE follow_up_events
                SET status = 'resolved', user_response = 'marked_taken_on_dashboard'
                WHERE user_id = ? AND medication_id = ? AND scheduled_date = ? AND status = 'pending'
                """,
                (user_id, med_id, target_date),
            )

        # If marked 'missed', check if caregiver alert threshold is reached
        caregiver_triggered = None
        if req.status == "missed":
            cg = conn.execute("SELECT * FROM caregivers WHERE user_id = ?", (user_id,)).fetchone()
            if cg and cg["enabled"] and cg["consent_given"]:
                missed_today = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt FROM medication_logs
                    WHERE user_id = ? AND scheduled_date = ? AND status = 'missed'
                    """,
                    (user_id, target_date),
                ).fetchone()["cnt"]
                recent_missed = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt FROM (
                        SELECT status FROM medication_logs
                        WHERE user_id = ? ORDER BY scheduled_date DESC, scheduled_time DESC LIMIT 9
                    ) WHERE status = 'missed'
                    """,
                    (user_id,),
                ).fetchone()["cnt"]

                if max(missed_today, recent_missed) >= cg["alert_threshold"]:
                    sim_msg = (
                        f"Caregiver notification triggered (SIMULATED MVP): Alert prepared for "
                        f"{cg['name']} ({cg['contact']}) after {max(missed_today, recent_missed)} missed doses "
                        f"(threshold: {cg['alert_threshold']})."
                    )
                    conn.execute(
                        """
                        INSERT INTO follow_up_events (
                            user_id, medication_id, scheduled_date, scheduled_time, event_type,
                            agent_observe, agent_reason, agent_plan, agent_act,
                            message, user_response, status, created_at
                        )
                        VALUES (?, ?, ?, ?, 'caregiver_alert_simulated', ?, ?, ?, ?, ?, 'auto', 'resolved', ?)
                        """,
                        (
                            user_id,
                            med_id,
                            target_date,
                            med["time"],
                            f"User marked {med['name']} as missed on {target_date}.",
                            f"Missed count ({max(missed_today, recent_missed)}) >= caregiver threshold ({cg['alert_threshold']}).",
                            "Trigger simulated caregiver notification per user consent.",
                            "Logged simulated caregiver alert in application.",
                            sim_msg,
                            now_str,
                        ),
                    )
                    caregiver_triggered = sim_msg

        conn.commit()

        today_logs = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM medication_logs WHERE user_id = ? AND scheduled_date = ?",
                (user_id, target_date),
            ).fetchall()
        ]
        metrics = compute_adherence_metrics(today_logs)

        return {
            "medication_id": med_id,
            "medication_name": med["name"],
            "status": req.status,
            "scheduled_date": target_date,
            "scheduled_time": med["time"],
            "timestamp": now_str,
            "adherence": metrics,
            "caregiver_notification_simulated": caregiver_triggered,
        }
    finally:
        conn.close()


# ============================================================================
# 4. ANALYTICS ENDPOINT
# ============================================================================

@app.get("/api/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    conn = get_connection()
    try:
        all_logs = [
            dict(r)
            for r in conn.execute(
                """
                SELECT ml.*, m.name AS medication_name, m.dosage
                FROM medication_logs ml
                JOIN medications m ON m.id = ml.medication_id
                WHERE ml.user_id = ?
                ORDER BY ml.scheduled_date DESC, ml.scheduled_time ASC
                """,
                (user_id,),
            ).fetchall()
        ]
        today_logs = [l for l in all_logs if l["scheduled_date"] == today_str]
        meds = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM medications WHERE user_id = ?", (user_id,)
            ).fetchall()
        ]

        overall_metrics = compute_adherence_metrics(all_logs)
        today_metrics = compute_adherence_metrics(today_logs)
        weekly_series = get_weekly_adherence_series(user_id)
        pattern_analysis = detect_adherence_patterns(all_logs, meds)
        agent_state = run_agent_cycle(user_id)

        return {
            "overall": overall_metrics,
            "today": today_metrics,
            "weekly_chart": weekly_series,
            "frequently_missed_time": pattern_analysis["frequently_missed_time"],
            "frequently_missed_period": pattern_analysis["frequently_missed_period"],
            "repeatedly_missed_medication": pattern_analysis["repeatedly_missed_medication"],
            "lowest_adherence_day": pattern_analysis["lowest_adherence_day"],
            "trend": pattern_analysis["trend"],
            "patterns": pattern_analysis["patterns"],
            "period_breakdown": pattern_analysis["period_breakdown"],
            "ai_adherence_insight": agent_state["adherence_insight"],
            "safety_notice": SAFETY_NOTICE,
        }
    finally:
        conn.close()


# ============================================================================
# 5. REMINDER SYSTEM ENDPOINT
# ============================================================================

@app.get("/api/reminders/due")
def get_due_reminders(current_user: dict = Depends(get_current_user)):
    """
    Return medications scheduled for today that are currently 'pending' so the
    frontend can trigger browser notifications or display the in-app reminder banner.
    """
    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    now_hm = datetime.now().strftime("%H:%M")

    conn = get_connection()
    try:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT
                    m.id AS medication_id,
                    m.name,
                    m.dosage,
                    m.time,
                    m.instructions,
                    COALESCE(ml.status, 'pending') AS status
                FROM medications m
                LEFT JOIN medication_logs ml
                    ON ml.medication_id = m.id AND ml.scheduled_date = ?
                WHERE m.user_id = ? AND m.start_date <= ? AND m.end_date >= ?
                ORDER BY m.time ASC
                """,
                (today_str, user_id, today_str, today_str),
            ).fetchall()
        ]
        pending_reminders = []
        for r in rows:
            if r["status"] == "pending":
                t_12 = format_time_12h(r["time"])
                is_due_now = r["time"] <= now_hm
                pending_reminders.append({
                    "medication_id": r["medication_id"],
                    "name": r["name"],
                    "dosage": r["dosage"],
                    "scheduled_time": r["time"],
                    "scheduled_time_12h": t_12,
                    "is_due_or_overdue": is_due_now,
                    "reminder_message": f"Time for {r['name']} ({r['dosage']}) — scheduled for {t_12}.",
                })
        return {
            "notifications_enabled": bool(current_user.get("notifications_enabled", 1)),
            "reminders": pending_reminders,
        }
    finally:
        conn.close()


# ============================================================================
# 6. AGENTIC AI & AI ASSISTANT ENDPOINTS
# ============================================================================

@app.get("/api/ai/state")
def get_ai_agent_state(current_user: dict = Depends(get_current_user)):
    """Return the complete OBSERVE -> REASON -> PLAN -> ACT -> REMEMBER state."""
    return run_agent_cycle(current_user["id"])


@app.post("/api/ai/followup-response")
def submit_followup_response(
    req: FollowUpResponseRequest, current_user: dict = Depends(get_current_user)
):
    result = handle_followup_response(
        user_id=current_user["id"],
        medication_id=req.medication_id,
        response_choice=req.response_choice,
        scheduled_date=req.scheduled_date,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    updated_agent = run_agent_cycle(current_user["id"])
    return {
        "result": result,
        "agent_state": updated_agent,
    }


@app.post("/api/ai/chat")
def assistant_chat(req: AssistantChatRequest, current_user: dict = Depends(get_current_user)):
    return handle_assistant_chat(current_user["id"], req.message)


@app.post("/api/ai/simulate-missed")
def simulate_missed_medication(current_user: dict = Depends(get_current_user)):
    """
    Helper for live college demonstration (Step 7 of Demo Flow):
    Simulates an unconfirmed/missed afternoon medication and triggers the AI follow-up
    and caregiver threshold check.
    """
    user_id = current_user["id"]
    today_str = datetime.now().date().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        meds = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM medications WHERE user_id = ? ORDER BY time ASC", (user_id,)
            ).fetchall()
        ]
        if not meds:
            raise HTTPException(status_code=400, detail="Add at least one medication first.")

        # Prefer Medicine B (14:00) if present, otherwise first medication
        target_med = next((m for m in meds if "Medicine B" in m["name"] or m["time"] == "14:00"), meds[0])

        conn.execute(
            """
            INSERT INTO medication_logs (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
            VALUES (?, ?, ?, ?, 'pending', ?)
            ON CONFLICT(medication_id, scheduled_date, scheduled_time)
            DO UPDATE SET status = 'pending', timestamp = excluded.timestamp
            """,
            (user_id, target_med["id"], today_str, target_med["time"], now_str),
        )
        t_12 = format_time_12h(target_med["time"])
        prompt_text = f"Your {t_12} medication ({target_med['name']} — {target_med['dosage']}) has not been confirmed. Did you take it?"

        conn.execute(
            """
            INSERT INTO follow_up_events (
                user_id, medication_id, scheduled_date, scheduled_time, event_type,
                agent_observe, agent_reason, agent_plan, agent_act,
                message, user_response, status, created_at
            )
            VALUES (?, ?, ?, ?, 'follow_up_prompt', ?, ?, ?, ?, ?, NULL, 'pending', ?)
            """,
            (
                user_id,
                target_med["id"],
                today_str,
                target_med["time"],
                f"Simulated overdue dose for {target_med['name']} ({t_12}).",
                "Medication remains unconfirmed past its scheduled time.",
                "Prompt user via Agentic AI Follow-Up card.",
                "Created interactive confirmation prompt.",
                prompt_text,
                now_str,
            ),
        )
        conn.commit()
        return {
            "message": f"Simulated unconfirmed dose for {target_med['name']} ({t_12}). Open AI Assistant to respond!",
            "agent_state": run_agent_cycle(user_id, current_time_24h="23:59"),
        }
    finally:
        conn.close()


# ============================================================================
# 7. TRUSTED CAREGIVER ENDPOINTS
# ============================================================================

@app.get("/api/caregiver")
def get_caregiver(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM caregivers WHERE user_id = ?", (user_id,)).fetchone()
        events = [
            dict(r)
            for r in conn.execute(
                """
                SELECT * FROM follow_up_events
                WHERE user_id = ? AND event_type = 'caregiver_alert_simulated'
                ORDER BY id DESC LIMIT 10
                """,
                (user_id,),
            ).fetchall()
        ]
        if not row:
            return {"caregiver": None, "simulated_alerts": events}
        cg = dict(row)
        cg["enabled"] = bool(cg["enabled"])
        cg["consent_given"] = bool(cg["consent_given"])
        return {"caregiver": cg, "simulated_alerts": events}
    finally:
        conn.close()


@app.put("/api/caregiver")
def upsert_caregiver(req: CaregiverUpdateRequest, current_user: dict = Depends(get_current_user)):
    if req.enabled and not req.consent_given:
        raise HTTPException(
            status_code=400,
            detail="User consent must be explicitly checked before enabling caregiver notifications.",
        )

    user_id = current_user["id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    consent_ts = now_str if req.consent_given else None

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO caregivers (user_id, name, contact, relationship, enabled, alert_threshold, consent_given, consent_timestamp, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                contact = excluded.contact,
                relationship = excluded.relationship,
                enabled = excluded.enabled,
                alert_threshold = excluded.alert_threshold,
                consent_given = excluded.consent_given,
                consent_timestamp = COALESCE(excluded.consent_timestamp, caregivers.consent_timestamp),
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                req.name.strip(),
                req.contact.strip(),
                (req.relationship or "Family Member").strip(),
                1 if req.enabled else 0,
                req.alert_threshold,
                1 if req.consent_given else 0,
                consent_ts,
                now_str,
            ),
        )
        conn.commit()
        cg = dict(conn.execute("SELECT * FROM caregivers WHERE user_id = ?", (user_id,)).fetchone())
        cg["enabled"] = bool(cg["enabled"])
        cg["consent_given"] = bool(cg["consent_given"])
        return {
            "caregiver": cg,
            "message": "Trusted caregiver configuration saved.",
        }
    finally:
        conn.close()


@app.delete("/api/caregiver")
def delete_caregiver(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    try:
        conn.execute("DELETE FROM caregivers WHERE user_id = ?", (user_id,))
        conn.commit()
        return {"message": "Trusted caregiver removed."}
    finally:
        conn.close()


@app.post("/api/caregiver/simulate-alert")
def simulate_caregiver_alert(current_user: dict = Depends(get_current_user)):
    """Trigger an in-app simulated caregiver notification when enabled and consented."""
    user_id = current_user["id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        cg = conn.execute("SELECT * FROM caregivers WHERE user_id = ?", (user_id,)).fetchone()
        if not cg:
            raise HTTPException(status_code=400, detail="Please add and save a caregiver first.")
        if not cg["enabled"] or not cg["consent_given"]:
            raise HTTPException(
                status_code=400,
                detail="Caregiver alerts must be enabled with user consent before triggering a notification.",
            )

        msg = (
            f"[SIMULATED MVP NOTIFICATION] Caregiver notification triggered to {cg['name']} "
            f"({cg['contact']}): 'Alex has reached the configured threshold of {cg['alert_threshold']} "
            f"missed medication doses. Please check in when convenient.'"
        )
        conn.execute(
            """
            INSERT INTO follow_up_events (
                user_id, medication_id, scheduled_date, scheduled_time, event_type,
                agent_observe, agent_reason, agent_plan, agent_act,
                message, user_response, status, created_at
            )
            VALUES (?, NULL, ?, '', 'caregiver_alert_simulated', ?, ?, ?, ?, ?, 'simulated_trigger', 'resolved', ?)
            """,
            (
                user_id,
                datetime.now().date().isoformat(),
                f"Missed dose count reached threshold ({cg['alert_threshold']}).",
                f"Caregiver alerts enabled=True and consent_given=True for {cg['name']}.",
                "Simulate caregiver notification inside the application (no SMS/WhatsApp per MVP rules).",
                "Triggered in-app simulated caregiver notification banner and log entry.",
                msg,
                now_str,
            ),
        )
        conn.commit()
        return {
            "simulated": True,
            "message": msg,
            "caregiver_name": cg["name"],
            "caregiver_contact": cg["contact"],
            "threshold": cg["alert_threshold"],
            "timestamp": now_str,
        }
    finally:
        conn.close()


# ============================================================================
# 8. SETTINGS ENDPOINTS
# ============================================================================

@app.get("/api/settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    return {
        "settings": {
            "name": current_user["name"],
            "email": current_user["email"],
            "notifications_enabled": bool(current_user["notifications_enabled"]),
            "follow_up_delay_minutes": current_user["follow_up_delay_minutes"],
            "timezone": current_user["timezone"],
        },
        "safety_notice": SAFETY_NOTICE,
    }


@app.put("/api/settings")
def update_settings(req: SettingsUpdateRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE users
            SET name = ?, notifications_enabled = ?, follow_up_delay_minutes = ?, timezone = ?
            WHERE id = ?
            """,
            (
                req.name.strip(),
                1 if req.notifications_enabled else 0,
                req.follow_up_delay_minutes,
                req.timezone.strip(),
                user_id,
            ),
        )
        conn.commit()
        return {
            "message": "Settings updated successfully.",
            "settings": {
                "name": req.name.strip(),
                "email": current_user["email"],
                "notifications_enabled": req.notifications_enabled,
                "follow_up_delay_minutes": req.follow_up_delay_minutes,
                "timezone": req.timezone.strip(),
            },
        }
    finally:
        conn.close()


# Serve Frontend Static App if built
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
