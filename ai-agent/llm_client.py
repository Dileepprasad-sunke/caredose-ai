"""
CareDose AI — LLM Client with Safe Fallback (ai-agent/llm_client.py)
Uses environment-configured LLM API (GEMINI_API_KEY or OPENAI_API_KEY) ONLY for:
- Friendly natural-language follow-up phrasing
- Non-medical adherence summaries
- Non-medical pattern explanations
Falls back seamlessly to deterministic templates if no API key is configured
or if network access is unavailable.
"""

import os
import requests
from datetime import datetime


def generate_natural_language_insight(
    adherence_pct: int,
    taken_count: int,
    missed_count: int,
    pending_count: int,
    primary_pattern: str,
    pending_med_names: list[str],
) -> dict:
    """
    Generate a friendly, non-medical adherence summary.
    Uses LLM API if GEMINI_API_KEY or OPENAI_API_KEY is set in environment;
    otherwise returns a clean, reliable deterministic response.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    # Deterministic fallback message (always safe, accurate, and fast)
    if pending_med_names:
        pending_str = ", ".join(pending_med_names)
        fallback_msg = (
            f"Today's adherence is {adherence_pct}% ({taken_count} taken, {missed_count} missed, "
            f"{pending_count} pending: {pending_str}). {primary_pattern}"
        )
    else:
        fallback_msg = (
            f"Great job tracking today! Your adherence is {adherence_pct}% "
            f"({taken_count} taken, {missed_count} missed). {primary_pattern}"
        )

    system_prompt = (
        "You are CareDose AI, a supportive medication adherence companion. "
        "Summarize the user's adherence stats in 2 concise, warm sentences. "
        "NEVER give medical advice, diagnoses, prescriptions, or dosing changes."
    )
    user_prompt = (
        f"Today stats: {adherence_pct}% adherence ({taken_count} taken, {missed_count} missed, "
        f"{pending_count} pending). Pattern detected: {primary_pattern}."
    )

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}]},
                timeout=4,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"text": text, "source": "llm_gemini", "generated_at": datetime.now().isoformat()}
        except Exception:
            pass

    if openai_key:
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 120,
                },
                timeout=4,
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                return {"text": text, "source": "llm_openai", "generated_at": datetime.now().isoformat()}
        except Exception:
            pass

    return {"text": fallback_msg, "source": "deterministic_engine", "generated_at": datetime.now().isoformat()}
