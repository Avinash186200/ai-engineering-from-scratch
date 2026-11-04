# Day 3, Part 1: What is an AI Agent? Workflows vs Agents and Tool Calling

**Watch:** [youtu.be/oqJixTE46QA](https://youtu.be/oqJixTE46QA) · **Code:** [`day03_agents/`](../day03_agents/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

What is an AI agent, really? In this episode we separate agents from ordinary workflows, open up the agent loop, and see exactly how a language model "uses a tool" without ever running anything itself.

## What you will learn

- Workflow vs agent: who decides the next step
- The spectrum from a single LLM call to multi-agent systems, and when NOT to build an agent
- The agent loop: model, tools, results, repeat
- Tool calling: who writes the tools, who chooses them, who runs them
- Why the tool description is the most important prompt in your system

## Chapters

- [0:00](https://youtu.be/oqJixTE46QA?t=0) Intro
- [0:28](https://youtu.be/oqJixTE46QA?t=28) Where we are in the series
- [1:14](https://youtu.be/oqJixTE46QA?t=74) Workflow versus agent
- [2:06](https://youtu.be/oqJixTE46QA?t=126) Worked example: workflow vs agent
- [3:04](https://youtu.be/oqJixTE46QA?t=184) The spectrum of autonomy
- [4:46](https://youtu.be/oqJixTE46QA?t=286) The agent loop
- [5:46](https://youtu.be/oqJixTE46QA?t=346) A real trace of the loop
- [6:49](https://youtu.be/oqJixTE46QA?t=409) Tool calling: who writes, who decides
- [8:09](https://youtu.be/oqJixTE46QA?t=489) Writing a good tool description

## Lesson notes

Slide content and the full narration, in order.

Hi, I'm Avinash, and welcome to day three of AI Engineering from Scratch. Today we build agents: language models that can use tools to get real work done. In this first part, we answer the basic question: what actually is an agent?

As always, if the pace feels slow, watch at one point two five times speed.

Quick look at the roadmap. On day one, we learned what a language model is. On day two, how to prompt it safely and get structured output. Today, day three, we teach it to use tools. Tomorrow, we plug those tools in through a standard called MCP.

Remember our research assistant chatbot. An analyst like Priya asks which funds look best on a date, and the numbers come from a fund ranking model, not from the language model's memory. Today we build the software that connects the two. That software is called an agent.

**The research assistant, so far**

> **User:** Which funds look best on 2025-06-20?
>
> **Assistant:** Top 3: Bharat Growth Fund +0.53%, Nifty Value Fund +0.51%, Deccan Bond Fund +0.49%.

## Workflow versus agent

Let's start with two words people mix up all the time: workflow, and agent.

A workflow is a sequence of steps the developer wrote in advance. The code decides what happens next. Think of booking a train ticket on IRCTC: the same screens, in the same order, every time. An LLM can be used inside a step, but it never chooses the step.

An agent is different. The model decides the next action while it runs. You give it a goal and a set of tools, which are just functions it may ask you to run. It looks at the situation, asks for a tool, sees the result, and decides again.

**Who decides the next step?**

- **Workflow**
  - Steps written in advance by the developer
  - The code decides what runs next
  - Like an IRCTC booking: same screens, same order
- **Agent**
  - The model decides the next action at runtime
  - Has a goal and a set of tools
  - Like a helpful colleague with a toolbox

*Same parts. The difference is who makes the decision.*

Here is a worked example. Rahul asks a two part question: rank the funds on a date, and also, what is an expense ratio? An expense ratio, by the way, is the yearly fee a fund charges, as a percentage of your money.

As a workflow, a classifier labels the question as a ranking question, the code calls the ranking tool, and the LLM writes the answer. The expense ratio half simply gets lost, because your fixed path only had one branch.

As an agent, the model reads the question and the list of tools, asks for the ranking tool and the definition tool, sees both results, and writes one answer covering both. Nobody wrote code saying, if the question has two parts, call two tools.

**One question, two halves**

1. Rahul asks: “Rank funds on 2025-06-20, and what is an expense ratio?”
2. Workflow: label it “ranking”, call the ranking tool, answer. Half is lost.
3. Agent: asks for rank_funds AND lookup_definition, then answers both

*Nobody coded “if the question has two parts, call two tools”.*

In practice, it is not a switch between two things. It is a spectrum. At the bottom, a single LLM call: summarise this report. Next, a fixed workflow, where the developer decides every step.

Then a router, where the model picks one of a few fixed paths, just once. Then a tool calling agent, where the model picks tools again and again, but within a limit. Our research assistant lives here.

At the top, multi agent systems, where models hand work to other models. Each level up buys flexibility, but costs predictability, speed, money, and ease of testing. So the rule is: use the lowest level that solves the problem.

**Five levels of autonomy**

| Level | Who decides the next step |
|---|---|
| 1. Single LLM call | Nobody: one step |
| 2. Fixed workflow | The developer, fully |
| 3. Router | Model picks one of N fixed paths, once |
| 4. Tool-calling agent | Model picks tools, repeatedly, within a limit |
| 5. Multi-agent | Models hand work to other models |

*Rule: use the lowest level that solves the problem.*

Interviewers love this question: when would you not build an agent? First, when the steps are known and fixed, like a nightly report. Second, when every answer must be exactly the same every time, like a tax calculation. That should be plain code.

Third, when speed matters, because every round of the loop is another model call of a second or more. Fourth, when the action cannot be undone, like sending money over UPI, and no human approves it first. And fifth, when you cannot test it. We cover testing on day six.

**When NOT to build an agent**

- The steps are known and fixed, like a nightly report
- Every answer must be exactly reproducible, like a tax calculation
- The latency budget is tight: each loop round is another model call
- The action is irreversible, like sending money over UPI, with no human check
- You have no test set to tell if a change made it better or worse

## The agent loop

Now let's open up the engine inside every agent. It is a surprisingly small loop.

Here it is. Keep a list of messages. Call the model with the system prompt, the messages, and the tool definitions. If the reply contains no tool calls, the model has chosen to answer, so we return its text. Otherwise, we run each requested tool, add the results to the messages, and go round again.

**The agent loop in pseudocode**

`pseudocode`
```python
messages = [user_question]
rounds = 0
loop:
    reply = model(system_prompt, messages, tools)
    messages.append(reply)
    if reply has no tool calls:
        return reply.text            # the model chose to answer
    if rounds == MAX_ROUNDS:
        stop safely                  # the limit
    for call in reply.tool_calls:
        try:    result = run_tool(call)
        except: result = {"error": "..."}   # failures become data
    messages.append(all results)
    rounds += 1
```

Read it as three roles. The model only ever produces text or a request, like, please run the ranking tool with these arguments. Your runtime, meaning the code around the model, actually runs the tool and catches failures. And the messages list is the memory that ties it all together.

**Who does what in the loop**

- The model: only produces text, or a request to run a tool
- Your runtime: runs the tool, catches failures, adds results
- The messages list: the memory every model call sees

*The model never executes anything. Your code decides.*

This is the most important idea of the day. The model never executes anything. It cannot touch your database or call your ranking model. It writes a structured request, and your code decides whether and how to honour it. That is what makes it safe to build on.

**Why tool calling is safe to build on**

> **The model writes a request. Your code decides whether to honour it.**
> It cannot touch your database or your ranking model directly. Every action passes through code you control.

Let's watch the messages for a simple question: what is an expense ratio? Message zero is the question. The model replies, not with prose, but with a tool use request: run lookup definition with the term expense ratio. It also gives this request an id, call one.

Our code runs the real Python function, which searches a glossary file. The result goes back tagged with the same id, call one, so the model knows which request it answers. One surprise: results go back in the user role, because to the model they come from outside.

Then the model is called again, with all three messages. Now it has the definition in front of it, so it answers in plain text. No tool call, so the loop ends. Two model calls, one tool call, four messages.

**One question, four messages**

> **User:** What is an expense ratio?
>
> **Assistant:** [tool_use id=call_1] lookup_definition(term="expense ratio")
>
> **Tool:** tool_result for call_1: {"term": "Expense ratio", "definition": "The yearly fee..."}
>
> **Assistant:** An expense ratio is the yearly fee a fund charges, as a % of your investment.

## Tool calling: who writes, who decides

Now the question that confuses most beginners. If the model never runs the tool, how does it choose one? And who writes what?

At design time, you, the developer, write everything the model will see: the real Python function, a name, a description, and a schema for the inputs. You also write the system prompt with the rules.

At runtime, the model decides which tool to call, if any, and fills in the argument values. Your runtime then runs the function and catches any errors. A simple way to remember it: you write the menu, the model orders from it, and your runtime does the cooking.

**Who writes what, who decides what**

| Thing | Who | When |
|---|---|---|
| The tool function (real Python) | Developer | Design time |
| Tool name, description, schema | Developer | Design time |
| The system prompt with rules | Developer | Design time |
| Which tool, and the argument values | Model | Runtime |
| Running it and catching errors | Your runtime | Runtime |

*You write the menu. The model orders. Your runtime cooks.*

So how does it choose? Remember day one: the model only predicts the next token. The tool definitions are inserted into its context as text it can read. During training, it saw many examples where the right next output was a tool call. So given this question and a tool described for rankings, the most likely output is a call to rank funds, with the date filled in.

**Choosing a tool is still next-word prediction**

**Tool list** (inserted into the model's context as text) → **Training** (model saw many examples of tool calls) → **Question** (“Which funds look best on 2025-06-20?”) → **Most likely output** (a call to rank_funds, with the date filled in)

Here is the actual tool definition from day three's agent dot py. A name. A description. And an input schema, written in JSON Schema, a standard way to describe the shape of some data: which fields, what types, which are required.

**Name, description, input schema**

`day03_agents/agent.py`
```python
{
  "name": "rank_funds",
  "description": (
    "Rank mutual funds by predicted return for one as-of date. "
    "Use for questions about which funds look attractive, "
    "rankings, scores or predicted returns. "
    "Dates must be YYYY-MM-DD business days."),
  "input_schema": {
    "type": "object",
    "properties": {
      "as_of": {"type": "string", "description": "YYYY-MM-DD"},
      "top_n": {"type": "integer", "description": "How many funds"}
    },
    "required": []
  }
}
```

Notice the three parts of that description. What it does. When to use it. And the constraints. Copy this pattern for every tool you write. A weak version, like, returns model output, leaves the model guessing whether a question like, what looks cheap today, belongs to this tool.

**A good description has three parts**

1. What it does: “Rank mutual funds by predicted return…”
2. When to use it: “Use for questions about which funds look attractive…”
3. Constraints: “Dates must be YYYY-MM-DD business days.”

*Weak version: “Returns model output.” The model is left guessing.*

Three consequences follow. One, the description is the most important prompt in the system. When the model picks the wrong tool, fix the description first, before changing models. Two, the schema constrains the arguments. Three, the model can still be wrong, so your code must check its requests.

**Three consequences**

- The description is the most important prompt in your system
- The schema constrains the arguments: types, formats, allowed values
- The model can still be wrong: validate, and return errors as results

A quick aside if you have done some machine learning. If not, just listen along. Choosing a tool is a classification problem, and filling in the arguments is structured extraction. Tool descriptions act like the class definitions you would give a human labeller. If they overlap or are vague, accuracy drops.

**The same ideas you may already know**

| Classic machine learning | The agent version |
|---|---|
| A classifier choosing a class | The model choosing a tool name |
| Extracting fields from text | The model filling in the arguments |
| Clear class definitions for labellers | Clear tool descriptions |

One common mistake to avoid in interviews: saying the model calls the API, or the model runs the function. It does neither. The model emits a request, and your runtime executes it. Interviewers listen for this, because every safety control is built on it.

**Say this precisely in interviews**

> **“The model runs the function.” Wrong.**
> The model emits a request. Your runtime executes it. Every safety control is built on that difference.

Quick check. Pause the video and think. Your agent keeps choosing the wrong tool for the question, what looks cheap today? What do you fix first? The answer: the tool descriptions. They are the only thing telling the model when to use each tool. Fix them before you reach for a bigger model.

**Quick check:** The agent keeps choosing the wrong tool for “what looks cheap today?”. What do you fix first?

<details><summary>Answer</summary>

The tool descriptions. They are the only text telling the model when to use each tool.

</details>

Let's recap. In a workflow, the code decides; in an agent, the model decides, within limits you set. Use the lowest level of autonomy that works. Every agent is one loop: model, tool calls, results, repeat. The model only requests; your code runs the tool. And good descriptions say what, when, and the constraints. Next, we turn this loop into a graph with LangGraph.

- Workflow: the code decides. Agent: the model decides, within limits
- Use the lowest level of autonomy that solves the problem
- The loop: model, tool calls, results, repeat until it answers
- The model only requests; your runtime runs the tool
- Tool descriptions: what it does, when to use it, constraints

The code for this video is in the day three agents folder, linked in the description. If this helped, subscribe, and I will see you in the next part.

---

← [Day 2, Part 4](day02_p4.md) · [All lessons](README.md) · [Day 3, Part 2](day03_p2.md) →
