# Day 16 lab: secure an AI application

Run from the repo root. No API key needed.

## Step 1: authentication and authorisation on the server
```bash
python day16_security/auth.py
```
Eight requests: no token, forged signature, expired token and a token whose role was edited to admin all get **401**.
A valid analyst can chat and read her own conversation; guessing someone else's conversation ID returns **404**
(not 403, so the attacker can't even confirm the ID exists). An admin can read any.
Try: change `ROLES` so analysts lose `chat`. Which status do they get now, and why is it 403 and not 401?

## Step 2: put a gate between the model and its tools
```bash
python day16_security/tool_policy.py
```
The model only **proposes** tool calls. Ordinary code decides: allowlist per role, argument validation (an SQL injection
attempt in the date is rejected), approved email domains, human confirmation for side effects, a per-user rate limit,
and an audit log of every decision.

## Step 3: watch an indirect prompt injection
```bash
python day16_security/injection.py
```
A factsheet contains hidden white text telling the assistant to email the conversation to an attacker.
1. No defences: the email is sent.
2. Spotlighting (marking the document as untrusted data) works, **if** the model respects it.
3. When the model ignores the markers, the email is sent again.
4. With the tool gate, the model is still fooled, but the action is denied.
Lesson: prompts and detectors **reduce** risk. Only code outside the model makes the bad action impossible.

## Step 4: keep secrets out of Git
```bash
python day16_security/secrets_scan.py --selftest
python day16_security/secrets_scan.py
```
The scanner prints where a secret is, never its value. Run it in CI and as a pre-commit hook.
If a real secret ever reaches Git: **rotate it first** (assume it is compromised), then clean history.

## Step 5 (exercise): close a gap
`/chat` in `auth.py` echoes the user's message. Add the Day 12 `leaks_pii` check so an answer containing an email or key is
blocked and logged. Then add a test for it (Day 15 style).

## The checklist for any AI feature
| Risk | Control |
|---|---|
| Anyone can call the API | Server-side authentication; tokens that expire |
| Users see each other's data | Ownership checks on every read; tenant filters in retrieval |
| Prompt injection (direct or via documents) | Untrusted-content marking, detection, and above all a tool policy gate |
| The agent does something irreversible | Side-effect tools need human confirmation; least-privilege tool credentials |
| Data leaves the company | Egress allowlists; no free-form URLs; redaction |
| Secrets leak | Secrets manager, scanning in CI, never in logs, rotation |
| Abuse and runaway cost | Rate limits and budgets per user |
| Nobody can investigate | Audit log of auth decisions and tool calls |
