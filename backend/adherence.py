"""
CareDose AI — Deterministic Adherence & Analytics Calculations (backend/adherence.py)
Implements Section 11 & 12:
Adherence percentage = (Taken scheduled doses / Total scheduled doses) * 100
Handles zero-dose cases safely and computes 7-day weekly chart series.
"""

from datetime import datetime, timedelta
from database.db import get_connection


def compute_adherence_metrics(logs: list[dict]) -> dict:
    """
    Calculate total scheduled, taken, missed, pending, and adherence percentage.
    Formula: Taken scheduled doses / Total scheduled doses * 100
    """
    total_scheduled = len(logs)
    taken_doses = sum(1 for l in logs if l.get("status") == "taken")
    missed_doses = sum(1 for l in logs if l.get("status") == "missed")
    pending_doses = sum(1 for l in logs if l.get("status") == "pending")

    if total_scheduled == 0:
        adherence_percentage = 0
    else:
        adherence_percentage = round((taken_doses / total_scheduled) * 100)

    return {
        "total_scheduled": total_scheduled,
        "taken_doses": taken_doses,
        "missed_doses": missed_doses,
        "pending_doses": pending_doses,
        "adherence_percentage": adherence_percentage,
    }


def get_weekly_adherence_series(user_id: int) -> dict:
    """
    Build a 7-day daily adherence breakdown (oldest to today) for Chart.js.
    """
    conn = get_connection()
    try:
        today = datetime.now().date()
        start_day = today - timedelta(days=6)
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT scheduled_date, status
                FROM medication_logs
                WHERE user_id = ? AND scheduled_date >= ? AND scheduled_date <= ?
                ORDER BY scheduled_date ASC
                """,
                (user_id, start_day.isoformat(), today.isoformat()),
            ).fetchall()
        ]

        labels = []
        dates = []
        adherence_pcts = []
        taken_counts = []
        missed_counts = []
        pending_counts = []

        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_str = d.isoformat()
            day_label = d.strftime("%a (%b %d)")
            day_logs = [r for r in rows if r["scheduled_date"] == d_str]
            metrics = compute_adherence_metrics(day_logs)

            dates.append(d_str)
            labels.append(day_label)
            adherence_pcts.append(metrics["adherence_percentage"])
            taken_counts.append(metrics["taken_doses"])
            missed_counts.append(metrics["missed_doses"])
            pending_counts.append(metrics["pending_doses"])

        return {
            "dates": dates,
            "labels": labels,
            "adherence_percentages": adherence_pcts,
            "taken_counts": taken_counts,
            "missed_counts": missed_counts,
            "pending_counts": pending_counts,
        }
    finally:
        conn.close()
