# Day 1, Part 4: How ChatGPT-style Models Are Trained: Pretraining, SFT, RLHF, DPO

**Watch:** [youtu.be/myaQsmeHTYQ](https://youtu.be/myaQsmeHTYQ) · **Code:** [`day01_llm_basics/`](../day01_llm_basics/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

A raw language model only continues text. So how does it become an assistant that answers questions, follows instructions and calls tools? This episode walks through every training stage, with real example records.

## What you will learn

- Pretraining and the base model, and why a base model is useless as a chatbot
- Supervised fine-tuning (SFT) with example training records and loss masking
- Why SFT teaches behaviour, not knowledge (a top interview question)
- Preference tuning: RLHF and DPO, with a worked preference pair
- Reasoning ("thinking") models and what the effort setting means

## Chapters

- [0:00](https://youtu.be/myaQsmeHTYQ?t=0) Intro
- [0:21](https://youtu.be/myaQsmeHTYQ?t=21) The three stages
- [1:04](https://youtu.be/myaQsmeHTYQ?t=64) Pretraining and the base model
- [2:04](https://youtu.be/myaQsmeHTYQ?t=124) Supervised fine-tuning (SFT)
- [4:42](https://youtu.be/myaQsmeHTYQ?t=282) RLHF and DPO, with a preference pair
- [7:40](https://youtu.be/myaQsmeHTYQ?t=460) Reasoning (thinking) models

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we went inside the transformer: embeddings, attention, and the final softmax. Today we ask how that machine is trained. Because a freshly trained model is not an assistant at all. Let me show you why.

A modern assistant is built in stages. The same network every time, but different data and a different goal. Stage one is pretraining: next word prediction on trillions of words, exactly what we saw in part one.

Stage two is supervised fine tuning. The model studies example conversations and learns to imitate good answers.

Stage three is preference tuning. The model sees pairs of answers, and learns to prefer the better one. Raw model in, helpful assistant out.

**Three training stages**

**Pretraining** (trillions of words; predict the next token) → **Fine-tuning (SFT)** (example conversations; imitate good answers) → **Preference tuning** (pairs of answers; prefer the better one)

*Base model → chat model → helpful, safe assistant.*

## Pretraining and the base model

Let's start with stage one.

Pretraining is next word prediction on a huge pile of books, websites and code. It is by far the most expensive stage, thousands of graphics chips running for weeks or months. The result is called a base model. It knows a great deal. But it has only ever learned to continue documents.

**Pretraining**

- Next-word prediction on books, websites and code
- By far the most expensive stage: thousands of GPUs for months
- Output: a base model that knows a lot, but only continues text

Watch what happens if you ask a base model a question. What is a mutual fund NAV?

It replies with more questions. What is an SIP? What is an expense ratio? Lists of questions are common on the internet, so that is a perfectly good next word prediction. But it is useless as an answer. Stages two and three fix exactly this.

**Ask a base model a question**

> **User:** What is a mutual fund NAV?
>
> **Assistant:** What is an SIP? What is an expense ratio? These questions often come up in interviews for...

## Supervised fine-tuning (SFT)

Stage two: supervised fine tuning, usually shortened to S F T.

We keep training the base model, but now on a much smaller, carefully chosen set of example conversations. Each one is a request plus the ideal reply, written or checked by a person. That is why it is called supervised. Think of a new employee studying a binder of model answers.

**Learning from example conversations**

- Keep training the base model on example conversations
- Each example: a request plus the ideal reply, written by a person
- Tens of thousands to a few hundred thousand examples

Here is what the data looks like. Each record is a short conversation, with roles: system for the instructions, user for the question, and assistant for the ideal reply. The first teaches it to answer a question. The second teaches it to summarise.

**Two SFT training records**

`sft_examples.jsonl (one example per line)`
```python
{"messages": [
  {"role": "system",    "content": "You are a helpful research assistant."},
  {"role": "user",      "content": "What is a mutual fund NAV?"},
  {"role": "assistant", "content": "NAV is the value of one unit of the
                       fund: total assets minus costs, divided by units."}
]}
{"messages": [
  {"role": "user",      "content": "Summarise this paragraph in one line: ..."},
  {"role": "assistant", "content": "The paragraph argues that ..."}
]}
```

*The model is graded only on the assistant's words.*

The training is the same next word prediction as before, with one twist. The model is only graded on the assistant's words. The question is given as context, but the model is not marked on predicting it. This is called loss masking. So it learns one thing: given this kind of request, produce this kind of reply.

**Loss masking**

> **Grade only the assistant's tokens**
> The system and user text is context. The model learns: given this request, produce this reply.

The examples cover many tasks: answering, summarising, writing code, refusing harmful requests, and asking clarifying questions. And one more that matters hugely for us: calling tools. Examples where the right reply is a structured tool call are how a model learns to use tools at all.

**SFT teaches many behaviours**

- Answer questions, summarise, write code
- Refuse harmful requests, ask clarifying questions
- Call tools: the reply is a structured tool call, not prose

Now a very common interview question. What does fine tuning change? Mainly behaviour and format. It teaches comparatively little new knowledge. So when someone asks, should we fine tune the model on our documents, the usual answer is no. Retrieval is the better tool for knowledge, as we will see on day five.

**What SFT changes, and what it doesn't**

- **Teaches**
  - Behaviour: answer, follow instructions
  - Format: JSON, tone, structure
  - Tool calls
- **Doesn't teach much**
  - New knowledge or facts
  - Correct numbers
  - Facts come from pretraining

*“Fine-tune on our documents?” Usually no: retrieval is better (Day 5).*

In the real product I built, we did not fine tune any model. We got behaviour from instructions, and knowledge from retrieval and tools. A prompt can be changed in minutes. A fine tuned model needs a fresh training run for every change. Fine tuning is the last lever, for a format or style you cannot get any other way.

**Fine-tuning is the last lever**

> **Behaviour from prompts. Knowledge from retrieval and tools.**
> Prompts change in minutes; every fine-tune needs a new training run. Fine-tune only for a format you can't get otherwise.

## Preference tuning: RLHF and DPO

Stage three. Why do we need another stage at all?

Writing a perfect answer is slow and expensive. But it is much easier for a person to look at two answers and say which one is better. Like a cricket selector, who cannot bat like Virat Kohli, but can certainly tell which of two innings was better. Preference tuning uses exactly that kind of judgement.

**Judging is easier than writing**

> **Easier to say “B is better than A” than to write the perfect answer**
> Like a cricket selector: they can't bat like Kohli, but they can tell which innings was better.

Here is one preference record for a fund assistant. The question: which fund should I buy today? Answer A says: buy Bharat Growth Fund, it will return zero point five three percent.

Answer B says: the ranking model puts Bharat Growth Fund first, with a predicted return of zero point five three percent. This is a research signal, not advice or a guarantee.

**Which fund should I buy today?**

> **User:** Which fund should I buy today?
>
> **Assistant:** A: Buy Bharat Growth Fund. It will return 0.53%.
>
> **Assistant:** B: The ranking model puts Bharat Growth Fund first, predicted +0.53%. This is a research signal from a tested model, not advice or a guarantee.

A reviewer marks B as better. A states a forecast as a fact, and gives an order. B says where the number came from, and is honest about uncertainty. Thousands of pairs like this teach the model the general preference, not just this one case.

**The reviewer picks B**

> **B is preferred: grounded and honest about uncertainty**
> A states a forecast as fact and gives an order. Thousands of pairs teach the general preference.

There are two main ways to use these pairs. The first is called R L H F, reinforcement learning from human feedback. Step one: collect prompts, let the model write two answers, and have people pick the better one.

Step two: train a separate model, called a reward model. It reads an answer and gives it a single score, trained so that the preferred answers score higher. Think of it as an automatic judge.

Step three: adjust the language model so its answers earn a high score from that judge. The risk to know by name is reward hacking. The model learns to fool the judge without really getting better. For example, writing long, flattering answers, because reviewers tended to prefer longer ones.

**RLHF: learning from human feedback**

1. Collect prompts; the model writes two answers; people pick the better one
2. Train a reward model: reads an answer, outputs a score
3. Adjust the LLM so its answers earn a high score

*Risk: reward hacking. Fooling the judge, e.g. long, flattering answers.*

The second method, from twenty twenty three, is D P O, direct preference optimisation. It uses the same pairs, but skips the judge entirely. It directly raises the probability of the preferred answer, and lowers the rejected one. It is simpler, cheaper and more stable, so many teams use it. In an interview: both use preference pairs. RLHF builds a judge. DPO trains directly on the pairs.

**DPO: skip the judge**

- **RLHF**
  - Learns a reward model (a judge)
  - Then optimises against it
  - Powerful, but complex
- **DPO**
  - Uses the same preference pairs
  - Trains directly: raise B, lower A
  - Simpler, cheaper, more stable

*Both use preference pairs. Only RLHF builds a separate judge.*

## Reasoning models

One more stage has appeared recently, and you will see it in every product.

Recent frontier models add practice on tasks whose answers can be checked automatically, like maths with a known answer, or code with tests. Correct answers are rewarded, and the model learns to write a long chain of reasoning before answering. In products, this appears as a thinking or effort setting. More thinking costs more tokens and time, and usually improves hard, multi step answers.

**Models that think before answering**

- Practise on tasks with checkable answers: maths, code with tests
- Reward correct final answers; the model learns to reason step by step
- In products: a “thinking” or “effort” setting

*More thinking = more tokens, more time, better hard answers.*

A few terms you will hear. A base model is the output of pretraining only. A chat, or instruction tuned model, has been through all the stages, and it is what every product uses. Alignment is the overall effort to make a model helpful, honest and harmless. And the knowledge cutoff is the date after which it saw no data at all.

**A few terms, in plain words**

| Term | Meaning |
|---|---|
| Base model | After pretraining only; continues text |
| Chat / instruction-tuned model | After SFT and preference tuning; what products use |
| Alignment | Making the model helpful, honest and harmless |
| Knowledge cutoff | The date after which it saw no training data |

Quick check. Pause and answer. A client says, let's fine tune the model on our fund factsheets, so it knows them. What do you say? The answer: fine tuning mainly teaches behaviour and format, not facts. Use retrieval for documents, and tools for numbers.

**Quick check:** A client says: “Let's fine-tune the model on our fund factsheets so it knows them.” What do you say?

<details><summary>Answer</summary>

Fine-tuning mainly teaches behaviour and format, not facts. Use retrieval for documents and tools for numbers.

</details>

Let's recap. Pretraining makes a base model that only continues text. Fine tuning on example conversations makes it answer, and it teaches behaviour, not knowledge. Preference tuning, with RLHF or DPO, teaches it to prefer better answers. And reasoning models learn to think first. In the final video for today: hallucination, sampling, and how to choose a model.

- Pretraining makes a base model that only continues text
- SFT trains on example conversations, graded on the reply only
- SFT teaches behaviour and format, not knowledge
- RLHF learns a judge from preference pairs; DPO trains on pairs directly
- Reasoning models are trained on checkable tasks to think first

The code for this series is linked in the description. Subscribe, and I will see you in the next video.

---

← [Day 1, Part 3](day01_p3.md) · [All lessons](README.md) · [Day 1, Part 5](day01_p5.md) →
