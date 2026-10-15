"""
CareDose AI — Explainable Adherence Pattern Detection (ai-agent/patterns.py)
Analyzes medication logs deterministically to identify:
- Frequently missed time windows (Morning / Afternoon / Evening) and specific times
- Repeatedly missed medications
- Lower-adherence days of the week
- Recent adherence trend (improving, steady, or declining)
No medical claims are ever made.
"""

from collections import defaultdict
from datetime import datetime


def format_time_12h(time_24h: str) -> str:
    """Convert '14:00' -> '2:00 PM' safely."""
    try:
        dt = datetime.strptime(time_24h.strip(), "%H:%M")
        return dt.strftime("%-I:%M %p")
    except Exception:
        return time_24h


def get_time_period(time_24h: str) -> str:
    """Classify HH:MM into Morning (<12:00), Afternoon (12:00-16:59), or Evening (>=17:00)."""
    try:
        hour = int(time_24h.strip().split(":")[0])
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        return "evening"
    except Exception:
        return "scheduled"


def detect_adherence_patterns(logs: list[dict], medications: list[dict]) -> dict:
    """
    Analyze historical medication logs and return explainable non-medical patterns.
    """
    med_lookup = {m["id"]: m for m in medications}

    if not logs:
        return {
            "frequently_missed_period": None,
            "frequently_missed_time": None,
            "repeatedly_missed_medication": None,
            "lowest_adherence_day": None,
            "trend": "insufficient_data",
            "primary_insight": "No adherence history recorded yet. Mark your scheduled doses as Taken or Missed to see personalized adherence patterns.",
            "patterns": [],
            "period_breakdown": {
                "morning": {"taken": 0, "missed": 0, "pending": 0, "total": 0, "adherence_pct": 0},
                "afternoon": {"taken": 0, "missed": 0, "pending": 0, "total": 0, "adherence_pct": 0},
                "evening": {"taken": 0, "missed": 0, "pending": 0, "total": 0, "adherence_pct": 0},
            },
        }

    period_stats = {
        "morning": {"taken": 0, "missed": 0, "pending": 0, "total": 0},
        "afternoon": {"taken": 0, "missed": 0, "pending": 0, "total": 0},
        "evening": {"taken": 0, "missed": 0, "pending": 0, "total": 0},
    }
    missed_by_time = defaultdict(int)
    missed_by_med = defaultdict(int)
    day_stats = defaultdict(lambda: {"taken": 0, "total": 0})
    date_stats = defaultdict(lambda: {"taken": 0, "total": 0})

    for log in logs:
        status = log.get("status", "pending")
        s_time = log.get("scheduled_time", "09:00")
        s_date = log.get("scheduled_date", "")
        med_id = log.get("medication_id")
        period = get_time_period(s_time)

        if period in period_stats:
            period_stats[period]["total"] += 1
            if status in ("taken", "missed", "pending"):
                period_stats[period][status] += 1

        if status == "missed":
            missed_by_time[s_time] += 1
            if med_id in med_lookup:
                missed_by_med[med_lookup[med_id]["name"]] += 1
            elif log.get("medication_name"):
                missed_by_med[log["medication_name"]] += 1

        if s_date:
            date_stats[s_date]["total"] += 1
            if status == "taken":
                date_stats[s_date]["taken"] += 1
            try:
                day_name = datetime.strptime(s_date, "%Y-%m-%d").strftime("%A")
                day_stats[day_name]["total"] += 1
                if status == "taken":
                    day_stats[day_name]["taken"] += 1
            except Exception:
                pass

    for p, st in period_stats.items():
        st["adherence_pct"] = round((st["taken"] / st["total"]) * 100) if st["total"] > 0 else 0

    patterns = []

    # 1. Frequently missed time period & exact slot
    frequently_missed_period = None
    frequently_missed_time = None
    most_missed_period_tuple = max(
        period_stats.items(), key=lambda kv: kv[1]["missed"], default=(None, {"missed": 0})
    )
    if most_missed_period_tuple[0] and most_missed_period_tuple[1]["missed"] > 0:
        frequently_missed_period = most_missed_period_tuple[0]

    if missed_by_time:
        top_time_24, top_time_count = max(missed_by_time.items(), key=lambda kv: kv[1])
        frequently_missed_time = format_time_12h(top_time_24)
        period_label = get_time_period(top_time_24)
        patterns.append({
            "type": "time_window",
            "title": f"Afternoon / {frequently_missed_time} Window Needs Attention" if period_label == "afternoon" else f"{frequently_missed_time} Schedule Pattern",
            "description": f"You frequently miss medications scheduled in the {period_label} ({frequently_missed_time}, missed {top_time_count} time{'s' if top_time_count != 1 else ''}).",
            "severity": "warning" if top_time_count >= 2 else "info",
        })

    # 2. Repeatedly missed medication
    repeatedly_missed_med = None
    if missed_by_med:
        top_med_name, top_med_count = max(missed_by_med.items(), key=lambda kv: kv[1])
        if top_med_count >= 2:
            repeatedly_missed_med = top_med_name
            patterns.append({
                "type": "repeated_medication",
                "title": f"Repeatedly Missed: {top_med_name}",
                "description": f"{top_med_name} was missed {top_med_count} times across your logged schedule. Consider pairing it with a daily routine.",
                "severity": "warning",
            })

    # 3. Lower-adherence day
    lowest_day = None
    if day_stats:
        day_rates = [
            (d, (vals["taken"] / vals["total"]) * 100)
            for d, vals in day_stats.items()
            if vals["total"] > 0
        ]
        if day_rates:
            lowest_day_name, lowest_rate = min(day_rates, key=lambda x: x[1])
            if lowest_rate < 100:
                lowest_day = lowest_day_name
                patterns.append({
                    "type": "day_of_week",
                    "title": f"Lower Adherence on {lowest_day_name}s",
                    "description": f"Your lowest adherence occurs on {lowest_day_name} ({round(lowest_rate)}% doses taken).",
                    "severity": "info",
                })

    # 4. Trend detection across dates
    sorted_dates = sorted(date_stats.keys())
    trend = "steady"
    if len(sorted_dates) >= 4:
        mid = len(sorted_dates) // 2
        early_dates = sorted_dates[:mid]
        recent_dates = sorted_dates[mid:]
        early_taken = sum(date_stats[d]["taken"] for d in early_dates)
        early_total = sum(date_stats[d]["total"] for d in early_dates)
        recent_taken = sum(date_stats[d]["taken"] for d in recent_dates)
        recent_total = sum(date_stats[d]["total"] for d in recent_dates)
        early_pct = (early_taken / early_total * 100) if early_total else 0
        recent_pct = (recent_taken / recent_total * 100) if recent_total else 0

        if recent_pct - early_pct >= 8:
            trend = "improving"
            patterns.append({
                "type": "trend",
                "title": "Adherence Trend: Improving",
                "description": f"Your recent adherence ({round(recent_pct)}%) improved compared to earlier days ({round(early_pct)}%).",
                "severity": "positive",
            })
        elif early_pct - recent_pct >= 8:
            trend = "declining"
            patterns.append({
                "type": "trend",
                "title": "Adherence Trend: Slight Dip",
                "description": f"Your recent adherence ({round(recent_pct)}%) is slightly lower than earlier in the week ({round(early_pct)}%).",
                "severity": "warning",
            })

    if not patterns:
        patterns.append({
            "type": "consistent",
            "title": "Strong Schedule Consistency",
            "description": "You are maintaining a consistent medication routine across all scheduled time windows.",
            "severity": "positive",
        })

    primary_insight = patterns[0]["description"]

    return {
        "frequently_missed_period": frequently_missed_period,
        "frequently_missed_time": frequently_missed_time or "None",
        "repeatedly_missed_medication": repeatedly_missed_med,
        "lowest_adherence_day": lowest_day,
        "trend": trend,
        "primary_insight": primary_insight,
        "patterns": patterns,
        "period_breakdown": period_stats,
    }
