# Day 8, Part 1: From Notebook to Product: LLM App Architecture, FastAPI and Docker

**Watch:** [youtu.be/8U4_Hdl5vxA](https://youtu.be/8U4_Hdl5vxA) · **Code:** [`day08_production/`](../day08_production/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Your chatbot works on your laptop. Now what? In this episode we look at everything around the model: the architecture of a real LLM product, a FastAPI /chat endpoint, and Docker from zero.

## What you will learn

- Why a product needs more than one Python script, and what each box in the architecture solves
- How a web framework like FastAPI turns a Python function into a /chat endpoint
- Why async code suits LLM requests, which mostly wait
- Docker images vs containers, layers and the build cache
- Why secrets must never be baked into an image

## Chapters

- [0:00](https://youtu.be/8U4_Hdl5vxA?t=0) Intro
- [0:30](https://youtu.be/8U4_Hdl5vxA?t=30) Where we are in the series
- [1:11](https://youtu.be/8U4_Hdl5vxA?t=71) Why a product needs an architecture
- [3:10](https://youtu.be/8U4_Hdl5vxA?t=190) FastAPI: a /chat endpoint
- [5:43](https://youtu.be/8U4_Hdl5vxA?t=343) Docker from zero

## Lesson notes

Slide content and the full narration, in order.

Hi, I am Avinash, and welcome to Day 8 of AI Engineering from Scratch. So far, our research assistant chatbot runs on one laptop. Today we learn how to turn it into a real product that many people can use at once.

As always, these videos are paced for learning. If it feels slow, watch at one point two five times speed.

Here is the roadmap. Days one to seven were about what happens inside an AI system: the model, prompts, agents, tools, retrieval and testing. Day eight is about everything around it: packaging, shipping, protecting, speeding up and keeping it running.

Why spend a whole day on this? Because a demo works once, for one person, on a good day. A product has to work for many people, every day, including the bad days. Interviewers know that, so they ask about it a lot.

**Interviewers spend a lot of time here**

- A demo works once, for one person
- A product works for many people, every day
- Production questions show you have actually shipped something

## Why a product needs an architecture

Let's start with the big picture. What does a real AI product look like, and why does it need so many pieces?

A notebook that calls an LLM is one Python program on one laptop, with one user: you. A product is different. Many analysts ask questions at the same time, over the internet, and expect answers in seconds. Conversations must survive a restart, and data must be protected while it travels.

**Two very different worlds**

- **Notebook**
  - One user: you
  - One laptop
  - Crashes? Just rerun
  - Key pasted in a cell
- **Product**
  - Hundreds of users at once
  - Answers in seconds
  - Must survive restarts
  - Data protected in transit

Here is the trick to learning architecture. Do not memorise boxes. Learn each box by the problem it solves. Then you can redraw the whole diagram from memory, and defend every box when an interviewer asks why it is there.

**Every box solves one problem**

> **Learn each component by the problem it solves.**
> Then you can redraw the diagram from memory and defend every box.

Here are the main boxes. A reverse proxy gives one safe, encrypted front door. The API service turns web requests into Python calls. A database keeps conversations. The tools, like our fund ranking model, give real numbers. And an adapter calls any LLM provider safely. We will cover each one today.

**The boxes, and the problem each solves**

| Component | Problem it solves |
|---|---|
| Reverse proxy + TLS | One safe, encrypted front door |
| API service (FastAPI) | Turns web requests into Python calls |
| Database (Postgres) | Conversations survive restarts |
| Tools (fund-ranking model) | Real numbers, not guesses |
| LLM adapter | One way to call any provider, safely |

Three words come up constantly. A service is a program that runs all the time and answers requests over the network. A replica is one of several identical copies of it. And stateless means a copy keeps nothing in its own memory that the next request needs. Think of IRCTC counters: any clerk can serve you, because your booking lives in the central system, not in one clerk's head.

**Service, replica, stateless**

- Service: a program that runs all the time and answers requests
- Replica: one of several identical copies running side by side
- Stateless: a copy remembers nothing the next request needs

## FastAPI: a /chat endpoint

Now let's build the front of our service: a web endpoint that an analyst's browser can talk to.

A browser talks to your service with H T T P. It sends a request, for example POST to slash chat, with a small JSON body holding the question. It gets back a response: a status code like two hundred for success, and a body with the answer. A web framework handles all this plumbing, so you just write a normal Python function.

**Request and response**

**Request** (POST /chat + JSON body) → **Your function** (runs the agent) → **Response** (status 200 + JSON answer)

*A web framework handles the plumbing.*

*You write a normal Python function.*

FastAPI is a popular Python web framework, and three features make it a good fit. Pydantic models, which we met on Day 2, check every request and reject bad input with status four two two. It publishes an automatic description of every endpoint. And it supports async code, which matters a lot for LLMs.

**Three features that suit LLM services**

- Pydantic models: bad input rejected with status 422, before your code runs
- Automatic schema at /openapi.json: docs and tests come for free
- Async support: one process serves many waiting requests

An LLM request spends almost all its time waiting: for the provider to generate tokens, for a tool, for the database. With async code, a request that is waiting hands control back, and the program serves someone else. It is like a chai stall owner taking new orders while the tea boils, instead of staring at the pot.

**LLM requests mostly wait**

> **While one request waits, serve the next.**
> Like a chai stall owner taking new orders while the tea boils.

Here is the core of app dot py. ChatRequest says every request must carry a thread id and a message of up to four thousand characters. Anything else is rejected automatically. Response model makes FastAPI check our own output too, so a bug that returns the wrong shape becomes an error instead of reaching Priya, our analyst. And notice the agent is built once at start-up, not for every request.

**A /chat endpoint**

`day08_production/app.py`
```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Research assistant chatbot")
agent = build_agent()          # built once, at start-up

class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    thread_id: str
    answer: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    answer = await agent.answer(req.thread_id, req.message)
    return ChatResponse(thread_id=req.thread_id, answer=answer)
```

Two more small endpoints are used by the platform, not by users. Liveness asks, is the program alive? If not, restart it. Readiness asks, can it serve traffic right now, for example, has it connected to the database? If not, stop sending it requests, but give it time. Run it yourself with uvicorn, and open slash docs in your browser.

**Two questions the platform asks**

- **/healthz (liveness)**
  - Is the process alive?
  - No: restart it
- **/readyz (readiness)**
  - Can it serve traffic now?
  - No: stop sending requests, don't restart

## Docker from zero

Our service runs on my laptop. Now, how do we get it onto a server, and make sure it runs exactly the same way there?

Every developer has said it: but it works on my machine! The server has a different Python, different packages, missing files. Installing by hand is slow and never quite identical. Docker solves this by packaging your program together with everything it needs, so it runs the same way everywhere.

**“It works on my machine”**

> **Package the program with everything it needs.**
> Python version, packages, model files and code travel together as one unit.

Two words to keep straight. An image is the package: a read-only snapshot of Python, your packages and your code. You build it once. A container is a running copy of an image. You can start many containers from one image, and when a container is removed, anything it wrote inside itself disappears.

**Image vs container**

- **Image**
  - The package: a read-only snapshot
  - Built once, has a name and tag
  - Like a recipe and its ingredients
- **Container**
  - A running copy of an image
  - Many from one image
  - Removed? What it wrote is gone

A container is not a virtual machine. A virtual machine pretends to be a whole computer, with its own operating system. A container shares the host's operating system core and is just walled off from other programs. That is why it starts in about a second, and you can run dozens on one server.

**A container is not a virtual machine**

- Virtual machine: pretends to be a whole computer, own operating system
- Container: shares the host's operating system core
- So containers start in about a second; dozens fit on one server

An image is built from a recipe called a Dockerfile. Each instruction makes one layer, and Docker caches every layer. When you rebuild, the first step that changed, and every step after it, is rebuilt. Packages change rarely; code changes all the time. So install packages first and copy your code last. That is the most common Dockerfile interview question, answered.

**How Docker rebuilds quickly**

1. Each Dockerfile instruction makes one layer
2. Docker caches every layer
3. First changed step and everything after it: rebuilt
4. So: install packages first, copy code last

Here is our Dockerfile. A slim Python base. The requirements file is copied and installed first, so edits to code reuse the cached packages. Then we copy only the folders we need. We create a normal user and run as that user, not as the all-powerful root. A health check, and finally the command that starts the server.

**Our Dockerfile**

`day08_production/Dockerfile`
```python
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY day08_production/ day08_production/

RUN useradd --create-home app
USER app

EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "day08_production.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

One rule you must never break. Never put an API key inside an image. Anyone who can download the image can unpack every layer, file by file, and deleting the file in a later layer does not remove it from the earlier one. Treat a key in an image as published. Keys arrive when the container starts, as we will see in the next part.

**No secrets in the image**

> **A key baked into an image is a published key.**
> Anyone who can pull the image can unpack every layer. Keys arrive at run time instead.

Two habits keep secrets out. Copy only the folders you name, never everything. And add a dot docker ignore file, which tells Docker to leave out environment files, keys and notebooks. Then try it: build the image with the command on screen, and run it with docker run.

**Two habits that keep secrets out**

- Copy named folders only, never COPY . .
- .dockerignore: leave out .env, keys, credentials, notebooks
- Run it: docker build -f day08_production/Dockerfile -t chatbot .

A real system has several containers: the API, the database, the tool server. Docker compose describes them all in one file and starts them together on a private network. Only the front door faces the internet, and the database keeps its data in a volume, storage that survives when containers come and go.

**docker compose**

- One YAML file describes the API, Postgres and the tool server
- docker compose up -d starts them all on a private network
- Only the proxy is open to the internet
- Postgres keeps its data in a volume that outlives containers

Quick check. Pause and answer: why do we copy the requirements file and install packages before copying the code? The answer: Docker caches layers. Code changes often and packages rarely, so a code edit reuses the cached install and the build takes seconds, not minutes.

**Quick check:** Why does a Dockerfile copy requirements.txt and install packages before copying the code?

<details><summary>Answer</summary>

Layers are cached. Code changes often, packages rarely, so a code edit reuses the cached install.

</details>

Let's recap. Every box in the architecture solves one problem. FastAPI with Pydantic gives us a validated chat endpoint. Async code serves others while a request waits. An image is the package, a container is a running copy. Install packages before code, and never put secrets in an image. Next, the front door, automatic checks, and where secrets really live.

- Every architecture box solves one problem
- FastAPI + Pydantic: a validated /chat endpoint
- Async: serve others while a request waits
- Image = package; container = running copy
- Packages before code; never secrets in an image

The code for this video is in the day eight production folder, linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 7, Part 4](day07_p4.md) · [All lessons](README.md) · [Day 8, Part 2](day08_p2.md) →
