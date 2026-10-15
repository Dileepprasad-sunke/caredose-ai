"""
CareDose AI — Simple MVP Authentication (backend/auth.py)
Provides salted PBKDF2-HMAC-SHA256 password hashing and signed HMAC session tokens.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional
from fastapi import Header, HTTPException, status
from database.db import get_connection
from database.seed import hash_password, verify_password

SECRET_KEY = os.environ.get("CAREDOSE_SECRET_KEY", "caredose-mvp-dev-secret-change-in-prod")
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


def create_access_token(user_id: int, email: str) -> str:
    """Create a lightweight HMAC-SHA256 signed token for MVP authentication."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{b64_payload}.{signature}"


def decode_access_token(token: str) -> Optional[dict]:
    """Verify signature and expiration of an access token."""
    try:
        if "." not in token:
            return None
        b64_payload, signature = token.split(".", 1)
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        padding = "=" * (-len(b64_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency that resolves and validates the logged-in user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
        )

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, name, email, notifications_enabled, follow_up_delay_minutes, timezone, created_at
            FROM users WHERE id = ?
            """,
            (payload["user_id"],),
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found.",
            )
        return dict(row)
    finally:
        conn.close()
