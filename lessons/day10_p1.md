# Day 10, Part 1: AI Engineer Technical Interview: Questions + Model Answers

**Watch:** [youtu.be/Y6tVgVUjuUA](https://youtu.be/Y6tVgVUjuUA) · **Code:** [`day10_mock/`](../day10_mock/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Day 10 is mock interview day. In this first part we run a full technical screen: how to set up a realistic mock, how to structure a two-minute answer, and model answers to the questions AI engineering interviewers ask most.

## What you will learn

- How to run a mock interview that actually tests you (recorded, timed, no notes)
- The three-part answer: definition, mechanism, example
- Model answers: LLMs, hallucination, temperature, JSON output, prompt injection
- Model answers: agents vs workflows, tool calling, golden sets
- What to say when you do not know the answer

## Chapters

- [0:00](https://youtu.be/Y6tVgVUjuUA?t=0) Intro
- [1:01](https://youtu.be/Y6tVgVUjuUA?t=61) How to run a mock that really tests you
- [2:43](https://youtu.be/Y6tVgVUjuUA?t=163) The shape of a strong answer
- [3:21](https://youtu.be/Y6tVgVUjuUA?t=201) Language model questions
- [3:33](https://youtu.be/Y6tVgVUjuUA?t=213) Q: What is an LLM?
- [4:14](https://youtu.be/Y6tVgVUjuUA?t=254) Q: Hallucination and temperature
- [5:14](https://youtu.be/Y6tVgVUjuUA?t=314) Prompting and safety questions
- [5:24](https://youtu.be/Y6tVgVUjuUA?t=324) Q: JSON output and prompt injection
- [6:27](https://youtu.be/Y6tVgVUjuUA?t=387) Agent and evaluation questions
- [6:39](https://youtu.be/Y6tVgVUjuUA?t=399) Q: Agents, tool calling, evals
- [8:06](https://youtu.be/Y6tVgVUjuUA?t=486) When you don't know

## Lesson notes

Slide content and the full narration, in order.

Hi, I am Avinash, and welcome to the final day of AI Engineering from Scratch. For nine days you learned the material. Today, we test it, with a full mock interview loop. This first part is the technical screen.

Here is the whole journey. Language models, prompting, agents, MCP, retrieval, testing, models, production, and system design. Today is the last stop: mock interviews, where every one of those days turns into answers you can say out loud.

A real interview loop usually has four kinds of round. A technical screen with short questions. A system design round with one big open problem. A coding round. And a behavioural round about how you work with people. We do one per video.

**Four rounds, like a real interview loop**

1. Technical screen: short questions, about 2 minutes each
2. System design: one big open problem in 35 minutes
3. Coding: build an agent and a retriever from a blank file
4. Behavioural: stories about how you work

## How to run a mock that really tests you

First, how to run a mock interview properly. Done badly, a mock just makes you feel good. Done well, it tells you the truth.

The idea is simple: remove every crutch you will not have on the real day. So no notes open. And answer out loud. Reading a good answer and producing one under pressure are two completely different skills.

Record yourself on your phone, and score from the recording. Memory is generous; recordings are not. Keep a timer visible. And no restarts. If you blank, say, let me take a moment to structure this, and carry on. Practising recovery is part of the exercise.

**Remove every crutch you won't have on the day**

- No notes: close everything except a blank file
- Out loud: speak every answer, never just type it
- Record yourself: score from the recording, not memory
- Timed: a visible timer, about 2 minutes per answer
- No restarts: if you blank, recover like you would live

And the most important rule. Pause this video before each model answer and try the question yourself first. If you read the answers before you attempt them, your score only measures your short term memory. It is like a cricket team practising only against bowlers they have already studied.

**Don't peek at the answers first**

> **Attempt the round first. Read the model answers after.**
> If you read them first, you are testing your short-term memory, not your skill.

Who plays the interviewer? An AI assistant works well. Open a fresh chat and ask it to play the interviewer: one question at a time, probe your answer once or twice, and score you at the end. Say your answer out loud first, for the recording, then type it in.

**Use an AI assistant as the interviewer**

> **User:** Act as my interviewer for an AI engineering technical screen. Ask one question at a time, probe once or twice, then score me.

## The shape of a strong answer

Before the questions, let's fix the shape of a good answer. Most people fail technical screens not on knowledge, but on structure.

A strong answer has three parts. A one sentence definition. Then the mechanism, how it works or what the trade off is. Then a concrete example, ideally from a project you built, like our research assistant chatbot. Then stop. Two minutes is about two hundred and fifty to three hundred spoken words.

**Three parts, about two minutes**

**1. Definition** (one sentence, plain words) → **2. Mechanism** (how it works, or the trade-off) → **3. Example** (a concrete case from a project)

*Then stop talking.*

*Two minutes is roughly 250 to 300 spoken words.*

## Language model questions

Now the questions. Remember: pause, answer out loud, then listen to the model answer. We start with language models.

Question one. What is a large language model, and how is it different from a normal prediction model? Pause and answer now.

**Quick check:** What is an LLM, and how is it different from a normal prediction model?

A model answer. An LLM is a neural network trained to predict the next token. At the output it is a very large classifier, run in a loop to write text. Knowledge emerges because it makes prediction easier. Its failure mode is a confident fabrication, so in our chatbot, the fund-ranking model produces every number and the LLM only explains.

**What is an LLM?**

- Definition: a network trained to predict the next token
- Mechanism: a classifier over ~100,000 tokens, run in a loop
- Abilities emerge because they make prediction easier
- Failure mode: a fluent, confident fabrication
- Example: in our chatbot the model ranks, the LLM explains

Next question: why do LLMs hallucinate? Because training rewards the plausible answer, not the true one, so a wrong number comes out exactly the same way as a right one. You cannot remove it, only contain it. Every number comes from a tool, and if the tool returns an error, the assistant says so. A common probe: does temperature zero fix it? No. Only grounding does.

**Why do LLMs hallucinate?**

- **Why**
  - Trained on plausible, not true
  - Nothing rewards “I don't know”
  - A wrong number comes out the same way as a right one
- **How we contain it**
  - Every number comes from a tool
  - Rule: never state a number no tool returned
  - Tool error? Say so, don't guess

*Probe: does temperature zero fix it? No. Grounding does.*

What are temperature and top p? Temperature reshapes the model's word probabilities: low makes the top choice dominate, high spreads them out. Top p cuts off the long tail of unlikely words. For a fund chatbot you want low randomness, so the same question gives the same tool call every time. Consistency over creativity.

**Temperature and top-p**

- Temperature: below 1 sharpens choices, above 1 flattens them
- Top-p: sample only from the most likely tokens adding up to p
- Factual or numeric work: low randomness, same question, same tool call
- Brainstorming: raise it

## Prompting and safety questions

Next, prompting and safety. These questions check whether you can make an LLM behave reliably in a real product.

How do you get reliable JSON out of a model? Three layers. First, constrain it, with the provider's structured output feature or a strict tool schema. Second, validate in code with Pydantic: types, ranges, required fields. Third, retry once with the error message, then fail loudly, rather than pass bad data on.

**How do you get reliable JSON out of a model?**

1. Constrain: use structured output or a strict tool schema
2. Validate in code: a Pydantic model checks types and ranges
3. Retry once with the error, then fail loudly

*Never parse model output with string matching.*

What is prompt injection? Untrusted text steering the model. Direct, when the user types ignore your rules. Indirect, when it hides inside a document the model reads. Telling the model to ignore injections is just more text. The real defence is architecture: label retrieved text as data, give user facing agents only read only tools, validate arguments, and keep injection cases in your test set.

**What is prompt injection?**

- **The attack**
  - Direct: user types “ignore your rules”
  - Indirect: hidden in a document or web page
  - The model can't reliably tell data from instructions
- **The defence**
  - Label retrieved text as data
  - Least privilege: read-only tools
  - Validate tool arguments; test injections in evals

*The defence is architecture, not a polite request in the prompt.*

## Agent and evaluation questions

Now agents and evaluation. Interviewers love these, because they separate people who have built something from people who have only read about it.

What is an agent, and when would you not build one? In a workflow, the developer fixes the steps in code. In an agent, the model chooses the next step at runtime. Agents handle open questions, but workflows are cheaper and more predictable. A nightly report that always runs the same three queries does not need an agent.

**Agent or workflow?**

|  | Workflow | Agent |
|---|---|---|
| Who picks the next step | The developer, in code | The model, at runtime |
| Good for | Known, fixed steps | Open-ended questions |
| Cost and speed | Cheaper, predictable | Slower, needs limits |

*Don't build an agent when the steps are known in advance.*

Walk me through one round of tool calling. My app sends the prompt and the tool schemas. The model decides: answer in text, or emit a tool call with arguments. My code, not the model, validates and runs the tool, and appends the result. Then the model reads it and answers. The model only proposes; my code executes.

**One round of tool calling: who does what**

**App sends** (prompt + tool schemas) → **Model decides** (answer, or a tool call) → **My code runs it** (validate, execute, append) → **Model again** (reads result, answers)

*The model only proposes. My code executes.*

*Probe: what most affects tool choice? The tool descriptions.*

What is a golden set? A version controlled list of test questions, each with the expected behaviour, like the right tool and the facts the answer must contain. Build it from real questions. Cover errors, out of scope requests and injection attacks. Keep a holdout you never tune on. And every production bug becomes a new case, so it cannot quietly come back.

**What is a golden set?**

- A version-controlled list of test questions + expected behaviour
- Built from real user questions, not invented ones
- Covers happy paths, errors, out-of-scope and injection cases
- Keep a holdout you never tune against
- Every production bug becomes a new case

Finally, what if you do not know? Never bluff. Interviewers probe exactly to find bluffs. Use this script: I have not used that directly, the problem it solves is this, I would evaluate it like this, and the closest thing I have done is that. Then stop talking.

**Never bluff. Use this script.**

> **“I haven't used that directly. The problem it solves is X. I'd evaluate it by Y. The closest thing I've done is Z.”**
> Then stop talking. A confident wrong answer costs far more than an honest gap.

Quick check. An interviewer asks, does setting temperature to zero stop hallucination? Pause and answer. The answer: no. It reduces randomness, but the model can still confidently state a plausible wrong fact. Grounding the answer in tools and documents is the fix.

**Quick check:** An interviewer asks: “Does setting temperature to zero stop hallucination?” What do you say?

<details><summary>Answer</summary>

No. It reduces randomness, but the model can still confidently state a wrong fact. Grounding answers in tools and documents is the fix.

</details>

Let's recap. Run mocks with no notes, out loud, recorded and timed. Attempt before you read the answers. Shape every answer as definition, mechanism, example, then stop. And when you do not know, say so and reason it through. In the next part: the system design round, minute by minute.

- Mock rules: no notes, out loud, recorded, timed, no restarts
- Attempt first, read model answers after
- Answer shape: definition, mechanism, example, stop
- Numbers from tools; injection defence is architecture
- Don't know? Say so, reason from first principles

The question bank and code are linked in the description. Practise three questions out loud today, and I will see you in the next part.

---

← [Day 9, Part 4](day09_p4.md) · [All lessons](README.md) · [Day 10, Part 2](day10_p2.md) →
