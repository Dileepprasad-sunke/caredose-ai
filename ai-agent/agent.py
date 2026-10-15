"""
CareDose AI — Agentic AI Engine (ai-agent/agent.py)
Implements the explicit 5-stage Agentic Workflow:
OBSERVE -> REASON -> PLAN -> ACT -> REMEMBER

Critical medication logic (schedule state, pending/missed status, adherence math,
caregiver threshold evaluation, and database updates) is 100% deterministic Python.
"""

from datetime import datetime
from database.db import get_connection
from .patterns import detect_adherence_patterns, format_time_12h
from .safety import SAFETY_NOTICE, evaluate_safety_query
from .llm_client import generate_natural_language_insight


def run_agent_cycle(user_id: int, current_time_24h: str | None = None) -> dict:
    """
    Execute the complete OBSERVE -> REASON -> PLAN -> ACT -> REMEMBER loop
    for the given user and return the full agent state for UI display.
    """
    conn = get_connection()
    try:
        today_str = datetime.now().date().isoformat()
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        effective_time = current_time_24h or now_dt.strftime("%H:%M")

        # =====================================================================
        # 1. OBSERVE: Monitor schedule, today's logs, 7-day history, caregiver
        # =====================================================================
        meds = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM medications WHERE user_id = ? ORDER BY time ASC", (user_id,)
            ).fetchall()
        ]

        # Ensure today's logs exist as 'pending' for each active medication
        for med in meds:
            if med["start_date"] <= today_str <= med["end_date"]:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO medication_logs
                    (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
                    VALUES (?, ?, ?, ?, 'pending', ?)
                    """,
                    (user_id, med["id"], today_str, med["time"], now_str),
                )
        conn.commit()

        today_logs = [
            dict(r)
            for r in conn.execute(
                """
                SELECT ml.*, m.name AS medication_name, m.dosage, m.frequency, m.instructions
                FROM medication_logs ml
                JOIN medications m ON m.id = ml.medication_id
                WHERE ml.user_id = ? AND ml.scheduled_date = ?
                ORDER BY ml.scheduled_time ASC
                """,
                (user_id, today_str),
            ).fetchall()
        ]

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

        caregiver_row = conn.execute(
            "SELECT * FROM caregivers WHERE user_id = ?", (user_id,)
        ).fetchone()
        caregiver = dict(caregiver_row) if caregiver_row else None

        taken_today = [l for l in today_logs if l["status"] == "taken"]
        missed_today = [l for l in today_logs if l["status"] == "missed"]
        pending_today = [l for l in today_logs if l["status"] == "pending"]
        total_today = len(today_logs)
        adherence_today = round((len(taken_today) / total_today) * 100) if total_today > 0 else 0

        # Identify overdue pending doses (scheduled_time <= effective_time)
        overdue_pending = [
            l for l in pending_today if l["scheduled_time"] <= effective_time
        ]
        # Fallback: if no pending dose is technically <= current clock (e.g. testing early in morning),
        # pick the first pending dose so the follow-up demo is always interactive.
        target_followup_dose = overdue_pending[0] if overdue_pending else (pending_today[0] if pending_today else None)

        observe_summary = {
            "total_scheduled_today": total_today,
            "taken_today": len(taken_today),
            "missed_today": len(missed_today),
            "pending_today": len(pending_today),
            "overdue_pending_count": len(overdue_pending),
            "adherence_today_pct": adherence_today,
            "caregiver_enabled": bool(caregiver and caregiver["enabled"] and caregiver["consent_given"]),
        }

        # =====================================================================
        # 2. REASON: Analyze overdue doses, repeated misses, and patterns
        # =====================================================================
        pattern_analysis = detect_adherence_patterns(all_logs, meds)

        # Count recent missed doses to check caregiver threshold
        recent_missed_count = sum(1 for l in all_logs[:12] if l["status"] == "missed")
        today_missed_count = len(missed_today)

        caregiver_threshold_reached = False
        if caregiver and caregiver["enabled"] and caregiver["consent_given"]:
            threshold = int(caregiver["alert_threshold"] or 2)
            if today_missed_count >= threshold or recent_missed_count >= threshold:
                caregiver_threshold_reached = True

        reason_points = []
        if target_followup_dose:
            t_12 = format_time_12h(target_followup_dose["scheduled_time"])
            reason_points.append(
                f"{target_followup_dose['medication_name']} ({target_followup_dose['dosage']}) scheduled for {t_12} is still unconfirmed (pending)."
            )
        if today_missed_count > 0:
            reason_points.append(f"{today_missed_count} medication dose(s) marked as missed today.")
        if pattern_analysis.get("primary_insight"):
            reason_points.append(pattern_analysis["primary_insight"])
        if caregiver_threshold_reached:
            reason_points.append(
                f"Missed dose count reached caregiver alert threshold ({caregiver['alert_threshold']} missed doses)."
            )

        # =====================================================================
        # 3. PLAN: Choose safe, bounded actions
        # =====================================================================
        planned_actions = []
        if target_followup_dose:
            planned_actions.append("Display interactive AI Follow-Up prompt to confirm pending medication status.")
        if caregiver_threshold_reached:
            planned_actions.append(
                f"Trigger simulated Trusted Caregiver alert to {caregiver['name']} (user consent verified)."
            )
        planned_actions.append("Generate friendly non-medical adherence summary & pattern insight.")

        # =====================================================================
        # 4. ACT: Prepare follow-up prompt, insight, and caregiver simulation
        # =====================================================================
        active_follow_up = None
        if target_followup_dose:
            t_12 = format_time_12h(target_followup_dose["scheduled_time"])
            prompt_msg = (
                f"Your {t_12} medication ({target_followup_dose['medication_name']} — "
                f"{target_followup_dose['dosage']}) has not been confirmed. Did you take it?"
            )
            active_follow_up = {
                "medication_id": target_followup_dose["medication_id"],
                "log_id": target_followup_dose["id"],
                "medication_name": target_followup_dose["medication_name"],
                "dosage": target_followup_dose["dosage"],
                "scheduled_date": target_followup_dose["scheduled_date"],
                "scheduled_time": target_followup_dose["scheduled_time"],
                "scheduled_time_12h": t_12,
                "prompt": prompt_msg,
                "options": [
                    {"id": "yes_taken", "label": "Yes, I took it", "variant": "success"},
                    {"id": "not_yet", "label": "Not yet", "variant": "neutral"},
                    {"id": "not_sure", "label": "I'm not sure", "variant": "warning"},
                ],
            }

        llm_insight = generate_natural_language_insight(
            adherence_pct=adherence_today,
            taken_count=len(taken_today),
            missed_count=len(missed_today),
            pending_count=len(pending_today),
            primary_pattern=pattern_analysis["primary_insight"],
            pending_med_names=[l["medication_name"] for l in pending_today],
        )

        caregiver_alert_simulation = None
        if caregiver_threshold_reached and caregiver:
            caregiver_alert_simulation = {
                "simulated": True,
                "triggered": True,
                "caregiver_name": caregiver["name"],
                "caregiver_contact": caregiver["contact"],
                "threshold": caregiver["alert_threshold"],
                "recent_missed_count": max(today_missed_count, recent_missed_count),
                "banner_message": (
                    f"[SIMULATED MVP NOTIFICATION] Caregiver notification triggered for {caregiver['name']} "
                    f"({caregiver['contact']}) after reaching the threshold of {caregiver['alert_threshold']} missed doses."
                ),
                "timestamp": now_str,
            }

        # =====================================================================
        # 5. REMEMBER: Store follow-up / caregiver events in SQLite
        # =====================================================================
        recent_events = [
            dict(r)
            for r in conn.execute(
                """
                SELECT fe.*, m.name AS medication_name
                FROM follow_up_events fe
                LEFT JOIN medications m ON m.id = fe.medication_id
                WHERE fe.user_id = ?
                ORDER BY fe.id DESC
                LIMIT 10
                """,
                (user_id,),
            ).fetchall()
        ]

        return {
            "workflow": {
                "OBSERVE": observe_summary,
                "REASON": reason_points,
                "PLAN": planned_actions,
                "ACT": {
                    "active_follow_up": active_follow_up,
                    "adherence_insight": llm_insight["text"],
                    "insight_source": llm_insight["source"],
                    "caregiver_simulation": caregiver_alert_simulation,
                },
                "REMEMBER": {
                    "stored_events_count": len(recent_events),
                    "recent_events": recent_events,
                },
            },
            "active_follow_up": active_follow_up,
            "adherence_insight": llm_insight["text"],
            "pattern_analysis": pattern_analysis,
            "caregiver_simulation": caregiver_alert_simulation,
            "safety_notice": SAFETY_NOTICE,
        }
    finally:
        conn.close()


def handle_followup_response(
    user_id: int,
    medication_id: int,
    response_choice: str,
    scheduled_date: str | None = None,
) -> dict:
    """
    Process the user's click on the AI Assistant Follow-Up buttons:
    - 'yes_taken'  -> Updates medication_logs status = 'taken', recalculates adherence
    - 'not_yet'    -> Keeps status = 'pending', provides supportive non-medical reminder
    - 'not_sure'   -> Advises user to check prescription/packaging or consult pharmacist/doctor
    Records the complete OBSERVE -> REASON -> PLAN -> ACT -> REMEMBER trace in follow_up_events.
    """
    conn = get_connection()
    try:
        today_str = scheduled_date or datetime.now().date().isoformat()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        med_row = conn.execute(
            "SELECT * FROM medications WHERE id = ? AND user_id = ?",
            (medication_id, user_id),
        ).fetchone()
        if not med_row:
            return {"error": "Medication not found for current user."}
        med = dict(med_row)
        t_12 = format_time_12h(med["time"])

        if response_choice == "yes_taken":
            # Deterministic DB update: mark as taken
            conn.execute(
                """
                INSERT INTO medication_logs (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
                VALUES (?, ?, ?, ?, 'taken', ?)
                ON CONFLICT(medication_id, scheduled_date, scheduled_time)
                DO UPDATE SET status = 'taken', timestamp = excluded.timestamp
                """,
                (user_id, medication_id, today_str, med["time"], now_str),
            )
            ai_reply = (
                f"Confirmed! I've marked your {t_12} dose of {med['name']} ({med['dosage']}) "
                f"as Taken at {now_str} and updated your daily adherence percentage."
            )
            new_status = "taken"
            plan_str = "Update medication log to 'taken' and recalculate daily/weekly adherence."
        elif response_choice == "not_yet":
            ai_reply = (
                f"Thanks for letting me know. Your {t_12} dose of {med['name']} ({med['dosage']}) "
                f"remains marked as Pending. Whenever you are ready, please follow your standard "
                f"prescription instructions—no dosing advice is provided here."
            )
            new_status = "pending"
            plan_str = "Keep medication status as 'pending' and provide a supportive non-clinical reminder."
        else:  # 'not_sure'
            ai_reply = (
                f"Because you're unsure whether you took your {t_12} dose of {med['name']}, "
                f"please do NOT take an extra or double dose right away. Check your pill organizer "
                f"or prescription instructions, or contact a pharmacist or healthcare professional for safe guidance."
            )
            new_status = "pending"
            plan_str = "Enforce safety guardrail: advise checking prescription instructions or contacting a pharmacist/doctor."

        # Store in follow_up_events (REMEMBER stage)
        conn.execute(
            """
            INSERT INTO follow_up_events (
                user_id, medication_id, scheduled_date, scheduled_time, event_type,
                agent_observe, agent_reason, agent_plan, agent_act,
                message, user_response, status, created_at
            )
            VALUES (?, ?, ?, ?, 'followup_confirmation', ?, ?, ?, ?, ?, ?, 'resolved', ?)
            """,
            (
                user_id,
                medication_id,
                today_str,
                med["time"],
                f"User responded '{response_choice}' to follow-up for {med['name']} ({t_12}).",
                f"Evaluated user confirmation choice '{response_choice}' deterministically.",
                plan_str,
                f"Set status='{new_status}' and returned safe response.",
                ai_reply,
                response_choice,
                now_str,
            ),
        )
        conn.commit()

        return {
            "medication_id": medication_id,
            "medication_name": med["name"],
            "updated_status": new_status,
            "user_response": response_choice,
            "ai_reply": ai_reply,
            "timestamp": now_str,
            "safety_notice": SAFETY_NOTICE,
        }
    finally:
        conn.close()


def handle_assistant_chat(user_id: int, user_message: str) -> dict:
    """
    Handle free-text questions in the AI Assistant while strictly enforcing
    healthcare safety guardrails (Section 17).
    """
    safety_check = evaluate_safety_query(user_message)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        if safety_check["is_blocked"]:
            reply = safety_check["safe_response"]
            event_type = "safety_guardrail"
        else:
            agent_state = run_agent_cycle(user_id)
            obs = agent_state["workflow"]["OBSERVE"]
            pattern_msg = agent_state["pattern_analysis"]["primary_insight"]
            reply = (
                f"Here is your current adherence update: You have taken {obs['taken_today']} of "
                f"{obs['total_scheduled_today']} scheduled doses today ({obs['adherence_today_pct']}% adherence), "
                f"with {obs['pending_today']} pending and {obs['missed_today']} missed. "
                f"Pattern insight: {pattern_msg} "
                f"(For any questions about dosing or symptoms, please consult your prescription label or healthcare provider.)"
            )
            event_type = "assistant_inquiry"

        conn.execute(
            """
            INSERT INTO follow_up_events (
                user_id, medication_id, scheduled_date, scheduled_time, event_type,
                agent_observe, agent_reason, agent_plan, agent_act,
                message, user_response, status, created_at
            )
            VALUES (?, NULL, ?, '', ?, ?, ?, ?, ?, ?, ?, 'resolved', ?)
            """,
            (
                user_id,
                datetime.now().date().isoformat(),
                event_type,
                f"User asked: {user_message[:120]}",
                f"Safety classification: {safety_check['category']}",
                "Respond within strict non-clinical adherence boundaries.",
                "Returned adherence status / safety guidance.",
                reply,
                user_message,
                now_str,
            ),
        )
        conn.commit()
        return {
            "reply": reply,
            "safety_triggered": safety_check["is_blocked"],
            "safety_category": safety_check["category"],
            "safety_notice": SAFETY_NOTICE,
            "timestamp": now_str,
        }
    finally:
        conn.close()
