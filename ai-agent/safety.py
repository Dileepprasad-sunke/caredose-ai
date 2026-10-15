"""
CareDose AI — Medical Safety Guardrails (ai-agent/safety.py)
Enforces strict healthcare boundaries so the AI never diagnoses, prescribes,
alters dosages, recommends doubling doses, or replaces medical professionals.
"""

SAFETY_NOTICE = (
    "CareDose AI is a medication adherence support tool. It does not provide "
    "medical diagnosis, prescriptions, dosage changes, or emergency medical advice."
)

EMERGENCY_KEYWORDS = [
    "overdose", "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "unconscious", "fainted", "severe allergic", "anaphylaxis", "emergency", "suicid",
]

DOSAGE_OR_MEDICAL_ADVICE_KEYWORDS = [
    "double dose", "double my dose", "take two", "take extra", "extra pill",
    "extra tablet", "what dose should i take", "how much should i take",
    "change my dose", "increase dose", "decrease dose", "stop taking",
    "skip my", "missed my dose what should i do", "missed dose what dose",
    "prescribe", "diagnose", "what disease", "side effect", "is it safe to mix",
    "interaction", "replace my medication", "switch medication",
]


def evaluate_safety_query(user_message: str) -> dict:
    """
    Check if a user's free-text message asks for medical advice, dosing changes,
    missed-dose clinical instructions, or emergency help.
    Returns {"is_blocked": bool, "category": str, "safe_response": str}
    """
    text = (user_message or "").strip().lower()

    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return {
                "is_blocked": True,
                "category": "emergency_boundary",
                "safe_response": (
                    "Important Safety Notice: CareDose AI cannot evaluate medical emergencies. "
                    "If you or someone else may be experiencing a medical emergency, please "
                    "contact local emergency services or a qualified healthcare provider immediately."
                ),
            }

    for kw in DOSAGE_OR_MEDICAL_ADVICE_KEYWORDS:
        if kw in text:
            return {
                "is_blocked": True,
                "category": "dosage_and_clinical_boundary",
                "safe_response": (
                    "I cannot recommend what dose to take, change your dosage, or advise whether "
                    "to take an extra or delayed dose. Please check your prescription label/medication "
                    "instructions or contact your pharmacist or healthcare professional for guidance."
                ),
            }

    return {
        "is_blocked": False,
        "category": "safe_adherence_query",
        "safe_response": "",
    }
