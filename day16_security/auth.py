"""Authentication and authorisation for an AI API, enforced on the SERVER.

  authentication = who are you?        -> a signed, expiring token (401 if missing or bad)
  authorisation  = what may you do?    -> roles and ownership checks (403 if not allowed)

Rules this file demonstrates:
  1. Never trust the client: hiding a button in the UI is not security. Every endpoint checks.
  2. Tokens are signed (HMAC) and expire; the signing key is a secret from the environment.
  3. Tenant isolation: a user can read only their own conversations, even by guessing an ID.
  4. The LLM never decides access. Permissions come from the token, not from the prompt.

Production systems use an identity provider (OAuth2/OIDC: Google, Entra ID, Okta, Auth0) and JWTs,
but the checks on the server are exactly these.

Run:  python day16_security/auth.py
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException

SECRET = os.environ.get("TOKEN_SIGNING_KEY", "dev-only-not-secret").encode()
ROLES = {"analyst": {"chat", "read_own"}, "admin": {"chat", "read_own", "read_any"}}


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def issue_token(user: str, role: str, ttl_s: int = 3600, now: float | None = None) -> str:
    body = _b64(json.dumps({"sub": user, "role": role, "exp": int((now or time.time()) + ttl_s)}).encode())
    sig = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token: str, now: float | None = None) -> dict:
    try:
        body, sig = token.split(".")
    except ValueError:
        raise HTTPException(401, "malformed token")
    expected = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):                 # constant-time compare
        raise HTTPException(401, "bad signature")
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    if claims["exp"] < (now or time.time()):
        raise HTTPException(401, "token expired")
    return claims


def current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    return verify_token(authorization.removeprefix("Bearer "))


def require(permission: str):
    def check(user: dict = Depends(current_user)) -> dict:
        if permission not in ROLES.get(user["role"], set()):
            raise HTTPException(403, f"role '{user['role']}' may not '{permission}'")
        return user
    return check


app = FastAPI(title="Day 16 secured API")
CONVERSATIONS = {"c-101": {"owner": "priya", "messages": ["Top funds on 2025-06-19?"]},
                 "c-202": {"owner": "rahul", "messages": ["What is an exit load?"]}}


@app.post("/chat")
def chat(body: dict, user: dict = Depends(require("chat"))):
    return {"user": user["sub"], "answer": f"(fake) answering: {str(body.get('message', ''))[:60]}"}


@app.get("/conversations/{cid}")
def get_conversation(cid: str, user: dict = Depends(current_user)):
    conv = CONVERSATIONS.get(cid)
    if conv is None:
        raise HTTPException(404, "not found")
    allowed = conv["owner"] == user["sub"] or "read_any" in ROLES.get(user["role"], set())
    if not allowed:
        raise HTTPException(404, "not found")       # 404, not 403: don't confirm the ID exists
    return conv


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    c = TestClient(app)
    priya = {"Authorization": "Bearer " + issue_token("priya", "analyst")}
    admin = {"Authorization": "Bearer " + issue_token("ops", "admin")}
    forged = issue_token("priya", "analyst").split(".")[0] + "." + "x" * 43
    expired = issue_token("priya", "analyst", ttl_s=-10)
    tampered_body = _b64(json.dumps({"sub": "priya", "role": "admin", "exp": 9999999999}).encode())
    tampered = tampered_body + "." + issue_token("priya", "analyst").split(".")[1]

    cases = [
        ("no token", c.post("/chat", json={"message": "hi"}), 401),
        ("forged signature", c.post("/chat", json={}, headers={"Authorization": "Bearer " + forged}), 401),
        ("expired token", c.post("/chat", json={}, headers={"Authorization": "Bearer " + expired}), 401),
        ("role edited to admin", c.post("/chat", json={}, headers={"Authorization": "Bearer " + tampered}), 401),
        ("valid analyst chats", c.post("/chat", json={"message": "hi"}, headers=priya), 200),
        ("priya reads her own conversation", c.get("/conversations/c-101", headers=priya), 200),
        ("priya guesses rahul's conversation", c.get("/conversations/c-202", headers=priya), 404),
        ("admin reads any conversation", c.get("/conversations/c-202", headers=admin), 200),
    ]
    for name, r, want in cases:
        print(f"  {name:36} -> {r.status_code}  {'ok' if r.status_code == want else 'WRONG'}")
        assert r.status_code == want, name
    print("ok: authentication and authorisation enforced on the server")
