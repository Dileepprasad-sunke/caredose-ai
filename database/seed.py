"""
CareDose AI — Demo Data Seeder (database/seed.py)
Populates the database with realistic demonstration data on first launch so
Dashboard, Analytics, Agentic AI Follow-Up, Pattern Detection, and Caregiver
workflows work out of the box.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from database.db import get_connection, init_db


def hash_password(password: str, salt: str | None = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2-HMAC-SHA256 hash."""
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), stored_hash)


def seed_demo_data(force_reset: bool = False) -> dict:
    """
    Seed the demo user (Alex Rivera, demo@caredose.ai / CareDose123!) and
    demonstration medications, 7-day logs, follow-up events, and caregiver config.
    """
    init_db()
    conn = get_connection()
    try:
        today = datetime.now().date()
        today_str = today.isoformat()
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@caredose.ai",)
        ).fetchone()

        if existing and not force_reset:
            return {"seeded": False, "user_id": existing["id"], "message": "Demo data already present."}

        if existing and force_reset:
            conn.execute("DELETE FROM users WHERE id = ?", (existing["id"],))
            conn.commit()

        # 1. Create Demo User
        pw_hash = hash_password("CareDose123!")
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password, notifications_enabled, follow_up_delay_minutes, timezone, created_at)
            VALUES (?, ?, ?, 1, 30, 'Asia/Kolkata', ?)
            """,
            ("Alex Rivera (Demo)", "demo@caredose.ai", pw_hash, now_iso),
        )
        user_id = cursor.lastrowid

        start_date = (today - timedelta(days=14)).isoformat()
        end_date = (today + timedelta(days=30)).isoformat()

        # 2. Insert Demo Medications matching prompt specification:
        # - Vitamin D, 500 mg, 9:00 AM (09:00)
        # - Medicine B, 1 tablet, 2:00 PM (14:00)
        # - Medicine C, 1 tablet, 8:00 PM (20:00)
        demo_meds = [
            ("Vitamin D", "500 mg", "Once Daily", "09:00", start_date, end_date, "Take with morning meal (Demo Data)", 1),
            ("Medicine B", "1 tablet", "Once Daily", "14:00", start_date, end_date, "Afternoon scheduled dose (Demo Data)", 1),
            ("Medicine C", "1 tablet", "Once Daily", "20:00", start_date, end_date, "Evening dose after dinner (Demo Data)", 1),
        ]

        med_ids = {}
        for name, dosage, freq, med_time, s_date, e_date, instr, is_demo in demo_meds:
            cur = conn.execute(
                """
                INSERT INTO medications (user_id, name, dosage, frequency, time, start_date, end_date, instructions, is_demo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, dosage, freq, med_time, s_date, e_date, instr, is_demo, now_iso),
            )
            med_ids[name] = cur.lastrowid

        # 3. Insert 6 prior days of historical logs to demonstrate weekly analytics & afternoon missed pattern
        # Pattern: Morning (09:00) and Evening (20:00) are consistently taken;
        # Afternoon (14:00 - Medicine B) was missed on 3 of the past 6 days so pattern detection identifies afternoon misses.
        historical_pattern = [
            # (days_ago, vit_d_status, med_b_status, med_c_status)
            (6, "taken", "taken", "taken"),
            (5, "taken", "missed", "taken"),
            (4, "taken", "taken", "taken"),
            (3, "taken", "missed", "taken"),
            (2, "taken", "taken", "missed"),
            (1, "taken", "missed", "taken"),
        ]

        for days_ago, s_vit, s_medb, s_medc in historical_pattern:
            d_str = (today - timedelta(days=days_ago)).isoformat()
            logs_to_insert = [
                (med_ids["Vitamin D"], d_str, "09:00", s_vit, f"{d_str} 09:05:00"),
                (med_ids["Medicine B"], d_str, "14:00", s_medb, f"{d_str} 14:45:00"),
                (med_ids["Medicine C"], d_str, "20:00", s_medc, f"{d_str} 20:10:00"),
            ]
            for m_id, s_date_log, s_time_log, status_val, ts_val in logs_to_insert:
                conn.execute(
                    """
                    INSERT INTO medication_logs (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, m_id, s_date_log, s_time_log, status_val, ts_val),
                )

        # 4. Insert Today's Medication Logs:
        # - Vitamin D (09:00): Taken
        # - Medicine B (14:00): Pending (overdue -> triggers AI follow-up!)
        # - Medicine C (20:00): Pending
        today_logs = [
            (med_ids["Vitamin D"], today_str, "09:00", "taken", f"{today_str} 09:04:12"),
            (med_ids["Medicine B"], today_str, "14:00", "pending", f"{today_str} 14:00:00"),
            (med_ids["Medicine C"], today_str, "20:00", "pending", f"{today_str} 20:00:00"),
        ]
        for m_id, s_date_log, s_time_log, status_val, ts_val in today_logs:
            conn.execute(
                """
                INSERT INTO medication_logs (user_id, medication_id, scheduled_date, scheduled_time, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, m_id, s_date_log, s_time_log, status_val, ts_val),
            )

        # 5. Seed Trusted Caregiver configuration (with user consent enabled)
        conn.execute(
            """
            INSERT INTO caregivers (user_id, name, contact, relationship, enabled, alert_threshold, consent_given, consent_timestamp, updated_at)
            VALUES (?, ?, ?, ?, 1, 2, 1, ?, ?)
            """,
            (
                user_id,
                "Priya Sharma (Demo Caregiver)",
                "priya.sharma@example.com | +91 98765 43210",
                "Sister / Primary Family Contact",
                now_iso,
                now_iso,
            ),
        )

        # 6. Seed an active Agentic AI Follow-Up Event for Medicine B (2:00 PM)
        conn.execute(
            """
            INSERT INTO follow_up_events (
                user_id, medication_id, scheduled_date, scheduled_time, event_type,
                agent_observe, agent_reason, agent_plan, agent_act,
                message, user_response, status, created_at
            )
            VALUES (?, ?, ?, '14:00', 'follow_up_prompt', ?, ?, ?, ?, ?, NULL, 'pending', ?)
            """,
            (
                user_id,
                med_ids["Medicine B"],
                today_str,
                "Observed Medicine B (1 tablet) scheduled at 2:00 PM is still 'pending' past its scheduled window.",
                "Afternoon doses (2:00 PM) have been missed 3 times in the past 6 days. Proactive check-in needed.",
                "Initiate non-judgmental AI follow-up prompt asking user to confirm status (Taken / Not yet / Unsure).",
                "Displayed interactive follow-up card in AI Assistant & Dashboard.",
                "Your 2:00 PM medication (Medicine B — 1 tablet) has not been confirmed. Did you take it?",
                now_iso,
            ),
        )

        conn.commit()
        return {"seeded": True, "user_id": user_id, "message": "Demo data seeded successfully."}
    finally:
        conn.close()
