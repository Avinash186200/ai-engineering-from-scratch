# Day 8, Part 2: HTTPS, Nginx, CI/CD and Secrets for LLM Apps, Explained Simply

**Watch:** [youtu.be/AOV_VMUM4P0](https://youtu.be/AOV_VMUM4P0) · **Code:** [`day08_production/`](../day08_production/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How does a real AI product protect its users, catch bugs before they ship, and keep API keys safe? This episode covers the front door and the safety net of an LLM application.

## What you will learn

- What TLS (the padlock) does, and why certificates must renew automatically
- What a reverse proxy like Nginx does, and two LLM-specific settings
- CI/CD: the automatic checks (gates) every change must pass
- Build once, deploy many: why prod runs the exact image you tested
- Configuration through environment variables, and the three rules for secrets

## Chapters

- [0:00](https://youtu.be/AOV_VMUM4P0?t=0) Intro
- [0:16](https://youtu.be/AOV_VMUM4P0?t=16) TLS: why the padlock matters
- [2:21](https://youtu.be/AOV_VMUM4P0?t=141) CI/CD: catching bugs before users do
- [6:21](https://youtu.be/AOV_VMUM4P0?t=381) Configuration and secrets

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part, we wrapped our research assistant chatbot in a FastAPI service and packed it into a Docker image. Now we put a safe front door on it, and a safety net under it.

## TLS: why the padlock matters

First, the front door. When Priya in Gurugram opens our chatbot, her question travels across the internet. Who else can read it?

TLS, the technology behind H T T P S and the padlock in your browser, does two jobs. It encrypts the traffic, so anyone in between sees only noise. And it proves the server is really yours, using a certificate, a signed statement from a trusted authority. Without it, passwords and portfolio questions cross the internet in plain text.

**Encrypt, and prove who you are**

- **Encrypts**
  - Anyone in between sees only noise
  - Passwords and questions stay private
- **Authenticates**
  - Server shows a certificate
  - Proves it really is your site

Let's Encrypt is a free, automated certificate authority. Its certificates last ninety days, so renewal must be automatic. If one expires, browsers show a scary warning, and many clients, like scripts or Excel, simply refuse to connect. It is a boring failure, and a very common one.

**Certificates expire**

> **Free certificates last 90 days. Renew automatically.**
> An expired certificate: browsers warn, and scripts or Excel simply refuse to connect.

A reverse proxy sits in front of all your services. Nginx is the most common one. It holds the certificate and decrypts the traffic. It routes, for example slash api to the chat service. It enforces limits like request size and rate. And it is the only thing facing the internet, so an attacker has much less to reach.

**One public door**

**Internet** (HTTPS from users) → **Nginx** (decrypts, routes, limits) → **/api/ to chat** (FastAPI service) → **Private network** (DB, tools: hidden)

*Only the proxy faces the internet.*

Two Nginx settings matter specially for LLM apps. First, the read timeout must be longer than your slowest genuine answer, otherwise Nginx cuts users off with a five oh four error. Second, if you stream tokens, turn buffering off, otherwise Nginx collects the whole answer and delivers it at the end, which defeats the purpose.

**Easy to get wrong**

- Read timeout longer than your slowest real answer, or users get 504
- If you stream tokens, turn buffering off
- Buffering on: the whole answer arrives at the end, all at once

## CI/CD: catching bugs before users do

Now the safety net. How do we stop a bad change from ever reaching users?

Continuous integration, or CI, means every proposed change, called a pull request, is automatically checked by programs before a human reviews it. Each check is a gate. If any gate fails, the change cannot be merged. Continuous delivery, or CD, turns merged code into an image and moves it through environments in a repeatable way.

**Continuous integration and delivery**

- **CI**
  - Every proposed change checked automatically
  - Each check is a gate
  - Red gate: cannot merge
- **CD**
  - Merged code becomes an image
  - Promoted dev, then prod
  - Same steps every time

Why does this matter even more for LLM apps? The code is mostly glue between many moving parts: an agent, tools, a provider, a database. Python only discovers many mistakes when the code runs. Gates turn whole classes of mistakes into a red cross on the pull request, instead of a failure in front of a user.

**The code is glue**

> **Gates turn whole classes of mistakes into a red cross.**
> Agent, tools, provider API, database: many moving parts, and Python only fails at run time.

Let's walk through the gates. mypy checks types without running the code. Imagine rank funds returns nothing for a fund with missing data. Without mypy, the code works in every test and crashes the first time an analyst asks about that fund. mypy forces you to handle the empty case.

Ruff is a fast linter. It catches common mistakes, and it can also ban imports. We ban direct provider libraries, so nobody can sneak in a quick call that skips our adapter, with its retries and logging. We will build that adapter in the next part.

pytest runs your normal tests. For example, asking about a Sunday must give a clear, not a business day, message, not a crash. Hypothesis goes further: you state a rule that must always hold, and it generates hundreds of strange inputs trying to break it.

And the gate most teams forget: the eval harness from Day 6. None of the other checks notice if the agent starts picking the wrong tool after a prompt change. Our eval harness exits with an error when the pass rate drops below ninety percent, so it can block the merge.

**What each check catches**

| Gate | Catches |
|---|---|
| mypy (types) | Using a value that might be None as if it were a number |
| Ruff (lint) | Unused imports, and banned direct provider SDK calls |
| pytest | Logic errors: a Sunday date must give a clear message |
| Hypothesis | Edge cases you never thought of, generated for you |
| Eval harness | Wrong tool or ungrounded numbers after a prompt change |

One more gate worth knowing: contract testing, with a tool such as Schemathesis. Remember the automatic schema FastAPI publishes? The tool reads it and fires hundreds of odd requests at the running service: empty strings, very long strings, strange Unicode, missing fields. The rule is simple. The service may reject bad input politely, but it must never crash with a five hundred error.

**Contract tests: does the API keep its promise?**

> **Fire hundreds of odd requests at the published schema.**
> Empty strings, huge strings, strange Unicode, missing fields. Rule: never a 500 error.

An environment is a full running copy of the system: dev for testing, prod for real users. The rule is build once, deploy many. CI builds one image, tagged with the commit, and that exact image goes to dev, gets checked, then goes to prod. Rebuilding for prod could pull a newer package you never tested. And keep the old image, so rolling back takes seconds.

**Ship the exact thing you tested**

**CI builds** (one image, tagged by commit) → **Dev** (same image, verified) → **Prod** (same image again)

*Only configuration differs between environments.*

*Keep the previous image: rollback takes seconds.*

Quick check. Pause and answer: why not just rebuild the image fresh for prod? The answer: a rebuild can pull a newer package or base image, so prod would run something you never tested. Deploy the identical image you verified on dev.

**Quick check:** Why not rebuild the image fresh when you deploy to prod?

<details><summary>Answer</summary>

A rebuild can pull newer packages, so prod would run something you never tested.

</details>

## Configuration and secrets

If the same image runs on dev and prod, how does it know which database to use, or which API key? Through configuration.

Configuration is everything that differs between environments: the database address, which provider and model to use, how much to log. The widely followed rule is to keep it out of the code and the image, and supply it as environment variables, named values the operating system hands to a program when it starts.

**Everything that differs between environments**

- Database address, provider and model names, log level, feature flags
- Kept out of the code and the image
- Supplied as environment variables when the container starts

In code, it is simple. We read the provider list, the log level and the key from the environment, with safe defaults. The default provider is the fake LLM from Day 3, so everything runs with no key and no cost. In prod, the values arrive from an env file or a secrets manager when the container starts.

**Reading configuration**

`day08_production/app.py`
```python
import os

PROVIDERS = os.environ.get("LLM_PROVIDERS", "fake").split(",")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")   # never printed

# run it:
# docker run --env-file prod.env -p 8000:8000 chatbot
```

A secret is configuration that grants access: API keys, database passwords. Three rules. Never in the repository, because git keeps history forever, so a key committed and then deleted is still there. Never in the image. And never in the logs, because logs are copied to many systems and read by many people.

**Three rules for API keys and passwords**

1. Never in the repository: git remembers forever
2. Never in the image: layers can be unpacked
3. Never in the logs: logs are copied everywhere

So where do they live? In a secrets manager, a service that stores them encrypted, controls who can read them, and records every access. In smaller setups, a locked-down file on the server. And plan for rotation: replacing a key regularly, and immediately if it ever leaks.

**Where secrets do live**

- A secrets manager: encrypted, access-controlled, every read recorded
- Or, in small setups, a locked-down env file on the server
- Rotation: replace a key regularly, and at once if it leaks

Here is a subtle trap. While debugging, it is tempting to print every variable whose name ends in U R L. But database connection strings carry the password right inside the address. Print names only, or mask the password part. It is a small habit that prevents a real leak.

**Never print variables by name pattern**

> **DATABASE_URL = postgres://user:PASSWORD@host/db**
> “Print everything ending in _URL” prints the password. Print names only, or mask it.

Let's recap. TLS encrypts traffic and proves who you are, and certificates must renew automatically. Nginx is the single public door. CI gates catch whole classes of bugs, including the eval harness. Build once and deploy the same image everywhere. And secrets never go in the repo, the image, or the logs. Next, the heart of reliability: the LLM adapter.

- TLS encrypts and proves identity; renew certificates automatically
- Nginx: one public door; long timeouts, no buffering for streams
- CI gates: types, lint, tests, property tests, evals
- Build once, deploy the same image to dev and prod
- Config in env vars; secrets never in repo, image or logs

The code is in the day eight production folder, linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 8, Part 1](day08_p1.md) · [All lessons](README.md) · [Day 8, Part 3](day08_p3.md) →
