# Day 4, Part 2: How MCP Works: JSON-RPC Messages, Lifecycle and Transports

**Watch:** [youtu.be/wGN5JHdYxtk](https://youtu.be/wGN5JHdYxtk) · **Code:** [`day04_mcp/`](../day04_mcp/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

What actually travels between an AI app and an MCP server? We read the real messages, step by step, and learn the two ways they travel.

## What you will learn

- JSON-RPC 2.0: the three message shapes MCP uses
- The full MCP lifecycle: initialize, tools/list, tools/call, shutdown
- Protocol errors vs tool errors, and why the difference matters
- stdio vs streamable HTTP transports
- The stdout bug that silently breaks stdio servers

## Chapters

- [0:00](https://youtu.be/wGN5JHdYxtk?t=0) Intro
- [0:18](https://youtu.be/wGN5JHdYxtk?t=18) The messages: JSON-RPC 2.0
- [1:51](https://youtu.be/wGN5JHdYxtk?t=111) The lifecycle, step by step
- [5:23](https://youtu.be/wGN5JHdYxtk?t=323) Transports: stdio and HTTP

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last video, we learned what MCP is: a standard so apps discover tools instead of hard wiring them, with a host, clients, and servers. Today, we open the wire and read the actual messages.

## The messages: JSON-RPC 2.0

First, what language do the client and server speak? MCP did not invent a new one. It borrowed a small, well-known standard.

Two terms. JSON is a simple text format for data, with names and values in curly brackets. RPC means remote procedure call: calling a function that lives in another program, as if it were local. JSON-RPC is a tiny, long established standard that combines the two. MCP uses it, so there are only three message shapes.

**JSON and RPC, in plain words**

- JSON: a simple text format for data, like {"fund": "Bharat Growth"}
- RPC: remote procedure call, calling a function in another program
- JSON-RPC 2.0: an old, tiny standard for RPC written in JSON
- MCP uses it, so there are only three message shapes to learn

A request says please do this, and carries an id number. A response says here is the answer to request number seven, using the same id. A notification is just so you know: no id, and no reply. The id matters, because several requests can be in flight at once, and replies are matched by id, not by order.

**Every MCP message is one of these**

| Shape | Has an id? | Reply expected? |
|---|---|---|
| Request: please do this | Yes | Yes |
| Response: here is the answer to request 7 | Yes, the same id | No |
| Notification: just so you know | No | No |

*The id lets many requests be in flight; replies are matched by id, not order.*

Here is a real tool call. Every message says JSON RPC two point oh. This is request number three. The method is tools slash call, and the params name the tool, rank funds, with its arguments: a date, and top three. That is all a tool call is on the wire.

**Calling a tool, as JSON-RPC**

`client -> server`
```python
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "rank_funds",
    "arguments": {"as_of": "2025-06-19", "top_n": 3}
  }
}
```

## The lifecycle, step by step

Interviewers often say: walk me through an MCP session from start to finish. Here is the lifecycle, the order of events from launch to answer.

Step one, connect. For a local server, the client simply launches it as a child program. For a remote server, the client opens a connection to its web address.

Step two, initialize. The client and server agree on a protocol version and declare what each one supports. That is like a handshake before a meeting. Then the client sends an initialized notification, and only now may real requests flow.

Step three, tools slash list. The client fetches every tool's name, description, and argument rules. The host converts them into the format its language model expects. This is the moment the model learns the tools exist.

Step four, the model asks for a tool, exactly like Day 3. Notice, the model never talks to the server. The host does, and it can check policy first, like, is this user allowed? Step five, tools slash call. The server checks the arguments, runs the function, and returns the result.

Step six, the answer. The host gives the result back to the model, which either calls another tool or writes the final reply. Step seven, shutdown. The connection closes and a local server simply exits.

**From connect to answer**

1. Connect: start the server, or open its web address
2. initialize: agree a protocol version and capabilities
3. tools/list: fetch the tools; the host shows them to the LLM
4. The LLM asks for a tool; the host checks policy
5. tools/call: the server validates, runs, returns the result
6. Answer: the LLM reads the result, calls again or replies
7. Shutdown: close the connection; the server exits

One practical point. Open the session once, when the app starts, and reuse it for every question. If you open a new stdio session per call, the server starts again and reloads the fund model every single time, which is slow. And a server with hundreds of tools can return its list in pages.

**Open once, reuse many times**

- Open the session once when the app starts
- Reuse it for every question the analyst asks
- A new stdio session per call = reload the model every time
- Big servers can split tools/list into pages with a cursor

Here is the response to request three. The result is a list of content blocks. Each block has a type, here text, holding the ranking as JSON. Our client reads it with json dot loads. And there is a flag called is error, which brings us to an interview favourite.

**What comes back from tools/call**

`server -> client`
```python
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {"type": "text",
       "text": "{\"top\": [{\"rank\": 1, \"fund\": \"Bharat Growth Fund\",
                 \"predicted_return\": 0.53}, ...]}"}
    ],
    "isError": false
  }
}
```

There are two kinds of error. A protocol error means the request itself is broken, like an unknown tool name, with a numeric code. The app handles it, and the model never sees it. A tool error means the tool ran, but could not answer, like a date that is a Sunday. That comes back with is error true and a readable message, so the model can retry with a weekday.

**Protocol error vs tool error**

- **Protocol error**
  - The request itself is broken
  - e.g. unknown tool, bad JSON
  - Code like -32601: method not found
  - Handled by the app, not the LLM
- **Tool error**
  - The tool ran but could not answer
  - e.g. date is a Sunday
  - isError: true, with a readable message
  - The LLM sees it and can fix it

Pause and answer. The analyst asks for rankings on a market holiday. Which kind of error should the server return? A tool error, with a clear message. That way, the language model reads it, and can explain the problem or retry with the nearest trading day.

**Quick check:** The analyst asks for rankings on a holiday. Which kind of error should the server return, and why?

<details><summary>Answer</summary>

A tool error (isError: true) with a clear message, so the LLM can read it, explain it, or retry with a nearby trading day.

</details>

## Transports: stdio and HTTP

The messages are always the same. A transport is just the pipe that carries them. MCP defines two.

The first is stdio, short for standard input and output. Every program has an input stream, an output stream, and an error stream for logs. The client starts the server and writes messages into its input. The server replies on its output, one line each. Nothing to deploy, no network. But only one client, on the same machine.

**stdio: a local pipe**

- Every program has stdin (input), stdout (output), stderr (logs)
- The client starts the server and writes messages to its stdin
- The server replies on stdout, one JSON message per line
- Good: nothing to deploy, no network, no ports
- Limit: one client per server, same machine only

Here is a bug that wastes days. In a stdio server, the output stream is the protocol channel. A stray print statement writes junk into it. Worse, Python holds output in a buffer, so the junk may appear hours later, in the middle of a reply. Intermittent errors in a stdio server are almost always this.

**Never print() in a stdio server**

> **stdout IS the protocol channel. A stray print() corrupts it.**
> Python buffers output in a pipe, so the bad text may appear hours later, mid-message. Log to stderr instead.

The fix is simple. Send all logs to the error stream, using the logging module. Never print to standard output. And watch out for libraries that print progress bars or messages when you import them.

**Log to stderr, never stdout**

`day04_mcp/fund_mcp_server.py`
```python
import logging, sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("fund-server")

# print("model loaded")          # WRONG: corrupts the protocol
log.info("model loaded")         # RIGHT: goes to stderr

# also watch for libraries that print progress bars on import
```

The second transport is streamable HTTP, for a shared server that a whole team uses. The server is a web service with one address, usually slash M C P. Each message is an HTTP post. For long jobs, the server can stream several replies back over time. Many clients can connect from anywhere, so now you need login and encryption.

**Streamable HTTP: a shared service**

- The server is a web service with one address, usually /mcp
- Each message is sent as an HTTP POST
- Long jobs can stream several replies back (SSE)
- Many clients, any machine, but needs login and TLS

Two details worth knowing. The HTTP server can hand the client a session id in a header, and the client sends it back on every later request, a bit like a token number at a bank counter. And you may meet older servers using a transport called HTTP plus SSE, with two endpoints. Streamable HTTP replaced it.

**Sessions, and an older transport**

- The server can hand out a session id in the Mcp-Session-Id header
- The client sends it back on every later request
- Older servers use HTTP+SSE: two endpoints instead of one
- Streamable HTTP replaced it; you may still meet the old one

And here is the payoff. In our server, switching from stdio to HTTP is one line. The tool code does not change at all, because the message format and the transport are separate. Run python day zero four underscore m c p slash m c p client dot py to see a full session yourself.

**Switching transport is one line**

`day04_mcp/fund_mcp_server.py`
```python
if __name__ == "__main__":
    mcp.run()                              # stdio: local, for development
    # mcp.run(transport="streamable-http") # shared web service
```

*The tool code does not change. Message format and transport are separate.*

Last check. Your whole team of analysts must share one fund server. Which transport? Streamable HTTP. Stdio serves only one client on one machine. HTTP serves many, as long as you add login and encryption.

**Quick check:** Your whole team of analysts must share one fund server. stdio or streamable HTTP?

<details><summary>Answer</summary>

Streamable HTTP: stdio is one client on one machine. HTTP serves many clients, with login and TLS.

</details>

Let's recap. MCP messages are JSON RPC: requests, responses, and notifications. The lifecycle runs connect, initialize, list, call, answer, shutdown. Protocol errors go to the app, tool errors go to the model. Use stdio for local tools and HTTP for shared ones. And never print in a stdio server. Next, we build the fund server ourselves.

- MCP messages are JSON-RPC: request, response, notification
- Lifecycle: connect, initialize, tools/list, tools/call, answer, shutdown
- Protocol errors go to the app; tool errors go to the LLM
- stdio for local tools; streamable HTTP for shared services
- Never print to stdout in a stdio server

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 4, Part 1](day04_p1.md) · [All lessons](README.md) · [Day 4, Part 3](day04_p3.md) →
