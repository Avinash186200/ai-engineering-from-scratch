"""Find secrets before they reach Git. Use it as a pre-commit check or a CI step.

Looks for common key formats, private keys, passwords in connection strings and suspicious assignments.
It prints WHERE a secret is, never the secret itself (a scanner that logs secrets is a leak too).
Production teams use gitleaks, trufflehog or GitHub secret scanning; the idea is identical.

Run:  python day16_security/secrets_scan.py            (scan this repo, exit 1 if anything is found)
      python day16_security/secrets_scan.py --selftest
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RULES = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Anthropic/OpenAI-style key": re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Password in a URL": re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:([^\s@/]{6,})@"),
    "Hard-coded secret": re.compile(r"(?i)\b(password|passwd|secret|api_key|token)\s*[:=]\s*['\"]([^'\"\s]{12,})['\"]"),
}
ALLOW = re.compile(r"(?i)example|dummy|placeholder|changeme|not-secret|fake|demo|xxxx|:password@|:secret@|\$\{|<[a-z_]+>")
SKIP_SUFFIX = {".png", ".jpg", ".mp4", ".db", ".xlsx", ".pdf", ".pyc"}


def scan_text(text: str, name: str = "<text>") -> list[tuple[str, int, str]]:
    found = []
    for i, line in enumerate(text.splitlines(), 1):
        for rule, rx in RULES.items():
            m = rx.search(line)
            if m and not ALLOW.search(m.group(0)):
                found.append((name, i, rule))
    return found


def repo_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
        return [root / p for p in out.splitlines()]
    except Exception:
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def _selftest() -> None:
    planted = "\n".join([
        'API_KEY = "sk-ant-' + "a1B2c3D4e5F6g7H8i9J0kLmN" + '"',
        "DATABASE_URL=postgresql://app:" + "S3cretPassw0rd" + "@10.0.0.5:5432/funds",
        "aws = 'AKIA" + "ABCDEFGHIJKLMNOP" + "'",
        'password = "changeme-example"',            # allowed: obviously a placeholder
        "TOKEN_SIGNING_KEY=${TOKEN_SIGNING_KEY}",    # allowed: a reference, not a value
    ])
    hits = scan_text(planted, "planted.env")
    for name, line, rule in hits:
        print(f"  {name}:{line}  {rule}")
    assert sorted({h[1] for h in hits}) == [1, 2, 3], hits
    print("selftest ok: 3 real-looking secrets found, 2 placeholders ignored, no values printed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
        sys.exit(0)
    root = Path(__file__).resolve().parent.parent
    hits = []
    for f in repo_files(root):
        if f.suffix.lower() in SKIP_SUFFIX or f.name == "secrets_scan.py" or not f.exists():
            continue
        try:
            hits += scan_text(f.read_text(encoding="utf-8", errors="ignore"), str(f.relative_to(root)))
        except OSError:
            continue
    for name, line, rule in hits:
        print(f"  {name}:{line}  {rule}")
    print(f"{len(hits)} possible secrets" if hits else "no secrets found")
    sys.exit(1 if hits else 0)
