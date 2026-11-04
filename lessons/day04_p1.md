# Day 4, Part 1: What is MCP (Model Context Protocol)? Explained Simply

**Watch:** [youtu.be/4Okj0ZCxmKg](https://youtu.be/4Okj0ZCxmKg) · **Code:** [`day04_mcp/`](../day04_mcp/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Your agent can call tools. But what happens when the tools live somewhere else, are owned by another team, and many apps need them? This is the problem the Model Context Protocol (MCP) solves.

## What you will learn

- The N x M integration problem, with an everyday analogy
- What MCP is, and the shift from wiring to discovery
- The three roles: host, client and server (and the two classic mix-ups)
- The three primitives: tools, resources and prompts, and who controls each

## Chapters

- [0:00](https://youtu.be/4Okj0ZCxmKg?t=0) Intro
- [0:31](https://youtu.be/4Okj0ZCxmKg?t=31) Where we are in the series
- [1:26](https://youtu.be/4Okj0ZCxmKg?t=86) The problem MCP solves
- [4:19](https://youtu.be/4Okj0ZCxmKg?t=259) Host, client and server
- [5:51](https://youtu.be/4Okj0ZCxmKg?t=351) Tools, resources and prompts

## Lesson notes

Slide content and the full narration, in order.

Hi, I am Avinash, and welcome to Day 4 of AI Engineering from Scratch. Today we learn MCP, the Model Context Protocol. It is the standard way to plug tools into any AI application, and interviewers love asking about it.

As always, no machine learning background is needed. And if the pace feels slow, watch at one point two five times speed.

Here is where we are. On Day 3, we built an agent: a language model that can decide to call tools. Today is Day 4, and we take those tools out of the agent's file and turn them into something any application can use.

Quick reminder of Day 3. Our research assistant chatbot called a tool named rank funds, which ranks mutual funds by predicted return. That tool was a Python function sitting in the same file as the agent, and we wrote its description by hand.

That works for one agent and three tools. Today's question is: what if the tool lives somewhere else, is owned by another team, and must be used by more than one application?

**The Day 3 agent**

- The agent called rank_funds, our fund-ranking tool
- The tool was a Python function in the same file as the agent
- We wrote its description and argument rules by hand
- Today's question: what if the tool lives somewhere else?

## The problem MCP solves

Let us start with the problem, because MCP only makes sense once you feel the pain it removes.

Imagine our chatbot becomes popular. Now three applications want the fund tools. The chatbot itself. A spreadsheet, because many analysts live in spreadsheets. And a notebook, where data scientists write Python.

And there are three tools: fund ranking, a risk check, and a fact sheet lookup. Without a standard, every app needs its own custom connection to every tool. Three times three is nine pieces of glue code, each with its own bugs.

**Who wants the fund tools?**

- **Apps (clients)**
  - The chatbot
  - A spreadsheet for analysts
  - A notebook for data scientists
- **Tools**
  - Fund ranking
  - Risk check
  - Fund fact sheet lookup

*3 apps x 3 tools = 9 pieces of custom glue code*

This is called the N times M problem. N apps times M tools gives N times M integrations. Each has its own way of passing arguments, returning errors, and logging in. Add one new tool, and every single app needs new code.

**Why custom glue does not scale**

> **N apps x M tools = N x M integrations**
> Each one with its own argument format, error format and login code. Add one tool, and every app needs new code.

Think of phone chargers. Years ago, every phone brand had its own charger, and your drawer was full of cables. Today, one USB-C port works with almost everything, because the phone and the charger agree on one connector. MCP is the USB-C port for AI tools.

**Think of phone chargers**

- Years ago: every phone brand had its own charger
- Today: one USB-C port works with almost everything
- MCP is the USB-C port for AI tools

So here is the definition. The Model Context Protocol is an open standard for how AI applications discover and use outside tools and data. A protocol simply means an agreed set of rules for a conversation between programs. It was published in late twenty twenty four and is now supported very widely.

**What MCP is**

> **An open standard for how AI apps discover and use outside tools and data**
> Published by Anthropic in late 2024, now supported widely. It fixes the message format, the order of messages, and how they travel.

The key idea is a shift from wiring to discovery. Without MCP, each app is told about each tool in its own code. With MCP, the app connects to a server and simply asks, what can you do? The server replies with a list of its tools. Add a new tool, and it just shows up.

**From wiring to discovery**

- **Without MCP**
  - The app is told about each tool in its own code
  - New tool = change every app
- **With MCP**
  - The app connects and asks: what can you do?
  - The server replies with its tool list
  - New tool = appears automatically

Quick check. Pause and answer. Four apps and five tools, without a standard: how many integrations? Without MCP, four times five, twenty. With MCP, each tool is wrapped once and each app learns MCP once. So roughly four plus five, nine pieces. Addition instead of multiplication.

**Quick check:** Four apps and five tools, without a standard. How many custom integrations? With MCP?

<details><summary>Answer</summary>

Without: 4 x 5 = 20. With MCP: each tool wrapped once, each app speaks MCP once: about 4 + 5 = 9.

</details>

## Host, client and server

MCP has three roles. The names are easy to mix up, so let us learn them with our chatbot in mind.

First, the host. The host is the AI application the user actually sees, and it is where the language model lives. In our project, the host is the research assistant chatbot.

Second, the client. A client is a small connector inside the host. It holds one connection to one server and speaks the protocol. In our code, that is the file mcp client dot py.

Third, the server. A server is a program that offers tools and runs them when asked. Ours is fund MCP server dot py, which wraps the fund ranking model. Think of a restaurant: the host is the restaurant, the client is the waiter, and the server is the kitchen.

**Who does what**

| Role | What it is | In our project |
|---|---|---|
| Host | The AI app the user sees; holds the LLM | The research assistant chatbot |
| Client | A connector inside the host, one per server | mcp_client.py |
| Server | A program that offers tools; runs them on request | fund_mcp_server.py |

Two mistakes people make in interviews. First, the server does not contain a language model. It is ordinary code: it gets a tool name and arguments, runs the function, and returns the result. Second, a host connected to three servers runs three clients, one each, and merges their tool lists for the model.

**What people get wrong**

- The server does NOT contain an LLM: it is ordinary code
- It receives a tool name and arguments, runs the function, returns the result
- One host with 3 servers runs 3 clients, one per connection
- The host merges all tool lists before showing them to the LLM

## Tools, resources and prompts

Now, what can a server actually offer? MCP defines three kinds of capability, called primitives.

The first and most important is a tool: a function the language model can call, like rank funds. The model itself decides when to call it. This is what you will use most, and what interviewers ask about most.

Second, a resource. A resource is read-only data with an address, like a web link. For example, a fund's fact sheet. The difference is control: the application decides to load a resource into the conversation, while the model decides to call a tool.

Third, a prompt. A prompt is a ready-made question template, shown to the user as a menu item, like Weekly fund briefing. The user picks it, types a date, and the template is filled in. So: tools for the model, resources for the app, prompts for the user.

**What a server can offer**

| Primitive | What it is | Who decides to use it |
|---|---|---|
| Tool | A function the LLM can call | The model |
| Resource | Read-only data with an address (URI) | The application |
| Prompt | A ready-made question template | The user |

*Remember it by who is in control: model, app, user.*

Tools can also carry hints called annotations. For example, read only, meaning it changes nothing, or destructive, meaning it may delete something. These help the app decide when to ask a human for approval. But a malicious server can lie, so they are hints, never security.

**Annotations: hints, not guarantees**

- readOnlyHint: the tool changes nothing
- destructiveHint: the tool may delete or overwrite
- idempotentHint: calling twice = calling once
- Hints help the app decide when to ask for approval
- A bad server can lie in them: never treat them as security

The protocol also works in the other direction. With sampling, a server borrows the host's language model, so it needs no API key of its own. With roots, the client tells the server which folders it may touch. With elicitation, the server asks the user for a missing input mid call. Know these names, but most real servers use tools only.

**When the server asks the client**

- Sampling: the server borrows the host's LLM to write text
- Roots: the client says which folders the server may touch
- Elicitation: the server asks the user for a missing input
- Know the names; most real servers use tools only

In a real product I built, this was the whole point. Each model was wrapped once as an MCP server. Then the chatbot, the spreadsheet, and the notebook all called the same server. So an analyst got exactly the same number in every app, from the same code. No copies that can quietly disagree.

**Why this matters at work**

> **Wrap each model once as an MCP server. Every app uses the same one.**
> The chatbot, a spreadsheet and a notebook all get the same numbers, from the same code.

Pause and answer. A fund fact sheet is attached to every chat automatically, before the analyst even asks. Tool, resource, or prompt? It is a resource. It is read only data, and the application, not the model, decided to load it.

**Quick check:** A fund fact sheet is attached to every chat automatically. Is that a tool, a resource or a prompt?

<details><summary>Answer</summary>

A resource: read-only data, and the application (not the model) decides to load it.

</details>

Let's recap. Custom glue between every app and every tool does not scale. MCP is a standard, so apps discover tools instead of hard wiring them. The host is the AI app, the client is a connector, and the server offers tools, with no language model inside. And the primitives are tools, resources, and prompts. Next, we open the wire and read the actual messages.

- N apps x M tools of custom glue does not scale
- MCP is a standard: apps discover tools instead of hard-wiring them
- Host = the AI app; client = one connector; server = offers tools
- The server has no LLM: it just runs functions
- Primitives: tools (model), resources (app), prompts (user)

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 3, Part 5](day03_p5.md) · [All lessons](README.md) · [Day 4, Part 2](day04_p2.md) →
