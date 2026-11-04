# Day 4, Part 3: Build an MCP Server in Python with FastMCP (Tool Design Tips)

**Watch:** [youtu.be/Pp4cWY8UY1A](https://youtu.be/Pp4cWY8UY1A) · **Code:** [`day04_mcp/`](../day04_mcp/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

We build a real MCP server for our research assistant chatbot in a few lines of Python, then learn how to design tools an LLM uses correctly.

## What you will learn

- How FastMCP turns a Python function into an MCP tool
- What a JSON Schema is, and how FastMCP generates it from type hints
- Why tool descriptions are prompts
- Six rules for good tools: errors as data, small outputs, read-only first
- MCP vs function calling vs REST vs OpenAPI, and the MCP-to-REST gateway

## Chapters

- [0:00](https://youtu.be/Pp4cWY8UY1A?t=0) Intro
- [0:19](https://youtu.be/Pp4cWY8UY1A?t=19) A server in a few lines
- [2:15](https://youtu.be/Pp4cWY8UY1A?t=135) The schema, made for you
- [4:06](https://youtu.be/Pp4cWY8UY1A?t=246) Designing good tools
- [5:46](https://youtu.be/Pp4cWY8UY1A?t=346) MCP vs REST, and the gateway

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time, we read the actual MCP messages and learned the two transports, stdio and HTTP. Today, we build the fund server ourselves, and learn how to design tools that a language model uses correctly.

## A server in a few lines

Let us write the server. The official Python library has a high level helper called FastMCP, and it makes this surprisingly short.

Here is the core of our server. We import FastMCP and our existing ranking function from core slash fund model dot py. We create a server, give it a name, and put the at mcp dot tool decorator on a small wrapper. A decorator is a label that registers the function as a tool. That is it.

**fund_mcp_server.py**

`day04_mcp/fund_mcp_server.py`
```python
from mcp.server.fastmcp import FastMCP
from core.fund_model import rank_funds as _rank_funds

mcp = FastMCP("fund-research")

@mcp.tool()
def rank_funds(as_of: str = "", top_n: int = 5) -> dict:
    """Rank mutual funds by predicted return on a date."""
    return _rank_funds(as_of, top_n)

if __name__ == "__main__":
    mcp.run()
```

Notice the structure. The ranking model knows nothing about language models, protocols, or chat. The tool is a one line wrapper. So when you retrain the model, no app changes. And when you change the interface, the model cannot change by accident. Each side can be tested on its own.

**Keep the model separate from the interface**

> **The model knows nothing about LLMs or protocols. The tool is a one-line wrapper.**
> Retrain the model: no app changes. Change the transport: the model is untouched.

And here is the client. It launches the server as a child program, initializes, lists the tools, and calls rank funds for the top three. You can see the lifecycle from the last video, in about ten lines. Run python day zero four underscore m c p slash m c p client dot py and you will see the tool list, then the ranking.

**Talking to the server**

`day04_mcp/mcp_client.py`
```python
params = StdioServerParameters(command=sys.executable,
                                args=["day04_mcp/fund_mcp_server.py"])

async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print([t.name for t in tools.tools])

        res = await session.call_tool("rank_funds", {"top_n": 3})
        print(json.loads(res.content[0].text))
```

So what does the decorator actually read? The tool's name comes from the function name. The description comes from the docstring, the text in triple quotes. The arguments come from the parameters and their type hints. And the defaults come along too, so calling with no arguments simply ranks funds on the latest date.

**Where each part of the tool comes from**

- Tool name: the function name, rank_funds
- Description: the docstring, the text in triple quotes
- Arguments: the parameters and their type hints
- Defaults: as_of empty means the latest date

## The schema, made for you

Now, how does the model know what arguments rank funds takes? Through something called a schema.

A JSON schema is a document that describes the shape of other JSON. Like a form with labelled boxes: which fields exist, their types, which are required, and which values are allowed. It does two jobs. It tells the model how to form a valid call. And it lets the server reject a bad call before running any code.

**What a JSON Schema is**

- A JSON document that describes the shape of other JSON
- Which fields exist, their types, which are required, allowed values
- Job 1: tells the LLM how to form a valid call
- Job 2: lets the server reject bad calls before running code

On Day 3, we wrote this by hand, and hand written schemas drift: someone adds a parameter and forgets the schema. FastMCP reads the function's type hints and builds the schema for you. String for the date, integer for top n. Change the function, and the schema follows.

**The schema FastMCP builds**

`tools/list -> inputSchema`
```python
{
  "type": "object",
  "properties": {
    "as_of": {"type": "string", "default": ""},
    "top_n": {"type": "integer", "default": 5}
  }
}
```

*No more drift: change the function, and the schema changes with it.*

But the basic schema says nothing about valid ranges. Top n equals five thousand would pass. So push the rules into the type hints, using Pydantic, the standard Python validation library. Now the date must look like a date, and top n must be between one and twenty. Bad calls are rejected with a clear message.

**Put the rules into the type hints**

`day04_mcp/fund_mcp_server.py`
```python
from typing import Annotated
from pydantic import Field

@mcp.tool()
def rank_funds(
    as_of: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$",
                     description="Trading day, YYYY-MM-DD")] = "",
    top_n: Annotated[int, Field(ge=1, le=20,
                     description="How many funds to return")] = 5,
) -> dict:
```

Pause and answer. The docstring says top n must be one to twenty, but the type hint is just int. Can the server reject five hundred? No. The model can read the prose, but the validator only enforces what is in the schema. Put the limit in the type hint.

**Quick check:** The docstring says 'top_n must be 1 to 20', but the type hint is just int. Can the server reject top_n=500?

<details><summary>Answer</summary>

No. The LLM can read the prose, but the validator only enforces what is in the schema. Put the limit in the type hint.

</details>

## Designing good tools

A tool is used by a model that cannot ask you what you meant. So every design choice should make the right call obvious, and the wrong call harmless.

The model picks a tool almost entirely by reading its name and description. So a description is a prompt. A weak one says, ranks funds. A strong one says when to use it, when not to, what inputs are valid, and how to read the output, like, these are predictions, not guarantees.

**Weak vs strong description**

- **Weak**
  - "Ranks funds."
- **Strong**
  - Use for: which funds look best on a date
  - Not for: fund definitions (use lookup)
  - Dates: trading days only
  - Returns are predictions, not guarantees

Here is a checklist. Clear names and descriptions. Valid ranges in the schema. Errors returned as data, like, that date is a Sunday, instead of a crash. Small outputs, because every byte goes into the model's context and costs tokens. Prefer read only tools that give the same answer every time, so they are safe to retry. And anything that acts, like sending money by UPI, needs a human to approve.

**Six rules for good tools**

1. Clear name and description: say when to use it
2. State valid ranges in the schema
3. Return errors as data, never crash
4. Keep outputs small: every byte costs tokens
5. Prefer read-only, repeatable tools
6. Put actions with side effects behind human approval

Let us see errors as data in action. If the ranking function crashes on a Sunday, the model learns nothing, and the analyst sees a broken chat. If it returns a small message, that date is a Sunday, the model reads it and retries with Friday, or explains the problem politely. Same bug, very different experience.

**Crash vs a helpful message**

- **Crash**
  - Exception, stack trace
  - The LLM learns nothing
  - The analyst sees a broken chat
- **Error as data**
  - {"error": "2025-06-22 is a Sunday"}
  - The LLM reads it
  - It retries with Friday, or explains

## MCP vs REST, and the gateway

A common interview question: how is MCP different from function calling, or from a normal web API? They are not rivals. They are layers.

Function calling is the model's ability to output a structured tool request. MCP is how the app then finds and calls that tool on a server. REST is an ordinary web API: send an HTTP request, get JSON back. And OpenAPI is a standard document that describes a REST API, like a menu card.

**Layers, not rivals**

| Term | What it is |
|---|---|
| Function calling | The LLM outputs a structured tool request |
| MCP | How an app discovers and calls tools on a server |
| REST | Ordinary web API: send HTTP, get JSON back |
| OpenAPI | A standard document that describes a REST API |

So why not use REST for everything? MCP adds things AI apps need. Every server answers the tool list the same way. Descriptions are written for a model, not a programmer. Results come shaped for the model, with an error flag. It works both ways, with progress updates. And it runs locally over stdio.

**What MCP adds for AI apps**

- Every server answers tools/list the same way: zero custom code
- Descriptions written for a model to choose between tools
- Results shaped for the model, with an isError flag
- Two-way features: progress, list changes, sampling
- Local servers over stdio, no web server needed

But spreadsheets and many business tools only speak plain web requests. They cannot speak MCP. Writing a separate API per model brings back the N times M problem. The fix is a gateway: a small proxy that connects to the MCP server, reads its tool list, and turns each tool into a web address, like post slash rank funds. It even generates the OpenAPI menu automatically.

**An MCP-to-REST gateway**

**Spreadsheet** (can call a web URL, cannot speak MCP) → **Gateway** (turns each tool into POST /rank_funds) → **MCP server** (the same fund server the chatbot uses) → **Fund model** (same code, same numbers)

*The spreadsheet sees plain REST. The numbers match the chatbot exactly.*

So Priya, an analyst in Gurugram, refreshes her spreadsheet. It sends a simple web request, and gets back the same top three funds the chatbot shows. Same server, same model function, same numbers. One implementation, every app.

**Plain REST, same numbers**

> **User:** POST /rank_funds   {"top_n": 3}
>
> **Tool:** 1. Bharat Growth Fund +0.53%  2. Nifty Value Fund +0.51%  3. Deccan Bond Fund +0.49%

In practice, a gateway gives you a lot for free. One web route per tool, built from the tool list. An OpenAPI document and a documentation page, generated automatically. And it can require an API key on every request. Just keep that key in a proper credential store, never typed into the spreadsheet itself.

**What the gateway gives you for free**

- One POST route per tool, built from tools/list
- An OpenAPI document and a /docs page, generated automatically
- Can require an API key on every request
- Keep the key in a credential store, not typed into the sheet

Last check. Why use a gateway instead of writing a separate REST API for the spreadsheet? Because a second API is a second code path, and two code paths can quietly disagree. The gateway reuses the very same server, so the numbers always match.

**Quick check:** Why use a gateway instead of writing a separate REST API for the spreadsheet?

<details><summary>Answer</summary>

A second API is a second code path that can disagree with the chatbot. The gateway reuses the same MCP server and model.

</details>

Let's recap. FastMCP turns a Python function into a tool with one decorator. Keep the model separate, with a thin wrapper. The schema comes from type hints, so put your limits there. Descriptions are prompts, errors are data, outputs stay small. And a gateway lets spreadsheets use the same tools. Next: security, testing, and plugging MCP into our agent.

- FastMCP: a decorator turns a Python function into an MCP tool
- Keep the model separate; the tool is a thin wrapper
- The schema is generated from type hints; put limits there
- Descriptions are prompts; return errors as data; keep outputs small
- A gateway exposes MCP tools as REST for spreadsheets

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 4, Part 2](day04_p2.md) · [All lessons](README.md) · [Day 4, Part 4](day04_p4.md) →
