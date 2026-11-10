# Day 16: Security for AI applications

What changes when software can be talked into things: authentication and authorisation on the server, a policy gate
between the model and its tools, indirect prompt injection and why prompts alone can't stop it, rate limits, audit logs,
and keeping secrets out of Git. Mapped to the OWASP Top 10 for LLM applications.

| Video | Short |
|---|---|
| [Day 16, full episode](https://youtu.be/4DQKs1686fc) | [One hidden line in a PDF can hijack your AI agent.](https://youtube.com/shorts/_-bUjq4o0s0) |

| File | What it is |
|---|---|
| [auth.py](auth.py) | Signed expiring tokens, roles, ownership checks: 401 vs 403 vs 404, enforced on the server |
| [tool_policy.py](tool_policy.py) | The model proposes, code decides: allowlist, argument validation, egress control, confirmation, rate limit, audit |
| [injection.py](injection.py) | An indirect prompt injection hidden in a document, and four layers of defence |
| [secrets_scan.py](secrets_scan.py) | A pre-commit / CI secrets scanner that never prints the secret |
| [LAB.md](LAB.md) | Five steps and a security checklist for any AI feature |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | Interview questions with full explanations and spoken answers |

## Quick start
```bash
python day16_security/auth.py
python day16_security/tool_policy.py
python day16_security/injection.py
python day16_security/secrets_scan.py --selftest
```

## Five lessons from a real production AI platform
1. Enforce access on the server. Restricting a login in the UI is not a control; the API must check every request.
2. The model never decides permissions. They come from the user's identity, outside the prompt.
3. Never print or log environment values. Connection URLs carry passwords.
4. A rotated secret is not rotated until the running service uses it and you have verified that.
5. Treat every document, web page and tool result as untrusted input to the model.
