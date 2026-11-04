# Day 7, Part 1: Prompt, RAG or Fine-Tune? When to Change an LLM's Weights

**Watch:** [youtu.be/IUBCmC0y59g](https://youtu.be/IUBCmC0y59g) · **Code:** [`day07_ml/`](../day07_ml/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Should you fine-tune a language model, or is a better prompt or retrieval the right fix? In this episode we learn the one distinction that answers that question almost every time: behaviour versus knowledge.

## What you will learn

- The three levers for adapting an LLM, and the order to reach for them
- Behaviour vs knowledge: what fine-tuning is good and bad at
- What full fine-tuning is, and why it needs so much memory
- How to prepare supervised fine-tuning data properly (and loss masking)
- Catastrophic forgetting, and how to limit it

## Chapters

- [0:00](https://youtu.be/IUBCmC0y59g?t=0) Intro
- [0:31](https://youtu.be/IUBCmC0y59g?t=31) Day 7: fine-tuning and validating models
- [1:12](https://youtu.be/IUBCmC0y59g?t=72) Three levers to adapt a model
- [2:14](https://youtu.be/IUBCmC0y59g?t=134) Behaviour versus knowledge
- [4:04](https://youtu.be/IUBCmC0y59g?t=244) Full fine-tuning, and why it is costly
- [5:23](https://youtu.be/IUBCmC0y59g?t=323) Preparing fine-tuning data properly
- [7:52](https://youtu.be/IUBCmC0y59g?t=472) Catastrophic forgetting

## Lesson notes

Slide content and the full narration, in order.

Hi, I'm Avinash, and welcome to Day 7 of AI Engineering from Scratch. Today has two halves. First, how to adapt a language model to your job. Then, how to check whether a model really works, or only looks like it works.

As always, these videos are paced for learning. If it feels slow, try one point two five times speed.

Here is where we are. We have built the chatbot, given it tools, connected documents, and learned to test it. Today, Day 7, is about the models themselves: adapting a language model, and validating the fund-ranking model properly.

Day 7 has four videos. This one answers the big question: when should you change a model's weights at all? Part two covers the cheap ways to do it. Parts three and four are about validation, the reason most impressive-looking results turn out to be wrong.

**The plan for Day 7**

- Part 1: prompt, retrieval or fine-tune? (this video)
- Part 2: LoRA, distillation and quantization
- Part 3: leakage and honest time-series testing
- Part 4: too many tries: deflated Sharpe and PBO

## Three levers to adapt a model

Let's start with a simple picture. A general model is like a smart new joiner at your office. How do you make them good at your job?

The first lever is the prompt. You simply tell the new joiner what you want: the format, the tone, the rules. It costs minutes to change.

The second lever is to hand it the right information when the question arrives. That is retrieval from Day 5 and tools from Day 3. Like giving the new joiner the right file before a meeting.

The third lever is fine-tuning: actually changing the numbers inside the model, its weights, by training it more. That is like sending the joiner on a three-month course. Powerful, but slow and expensive. Interviewers want to hear that you reach for these in this order.

**Three levers to adapt a model**

1. Change the prompt: tell it what you want
2. Give it knowledge at question time: retrieval and tools
3. Change the weights: fine-tuning

*Reach for them in this order.*

## Behaviour versus knowledge

So when is the third lever worth it? One distinction answers this almost every time: behaviour versus knowledge.

Behaviour is how the model answers. The format, the tone, the length, which tool it picks, or a narrow decision like, is this question about funds or not?

Knowledge is what facts it can use. The factsheet of Bharat Growth Fund, today's predicted returns, last week's research note. Different problem, different fix.

**Behaviour versus knowledge**

- **Behaviour**
  - HOW it answers
  - Format, tone, length
  - Which tool it picks
  - A narrow yes or no decision
- **Knowledge**
  - WHAT facts it can use
  - Fund factsheets
  - Today's fund numbers
  - Last week's research note

Fine-tuning is good at behaviour. Show the model a thousand examples of your exact report format, and it learns that format reliably.

But fine-tuning is bad at knowledge. Facts baked into weights cannot be cited, cannot be hidden from users who should not see them, and go stale the moment the document changes. Retrieval fetches the document at question time instead.

And live numbers, like today's predicted returns, come from a tool, our fund-ranking model. Here is the rule of thumb: updating knowledge should mean updating a database row, not running a new training job.

**What fine-tuning is good and bad at**

| Need | Best fix | Why |
|---|---|---|
| Strict output format | Prompt, then fine-tune | Behaviour: learned well from examples |
| Fund factsheets | Retrieval (RAG) | Can be cited, updated, permissioned |
| Today's predicted returns | A tool | Live numbers, computed exactly |

*Updating knowledge should mean updating a database row, not a training run.*

Here is a request you will hear in real projects. Priya, an analyst, asks: can you fine-tune the chatbot so it knows all our fund factsheets? The right answer is no. That is a knowledge request. Factsheets change every month and must be cited, so they belong in retrieval.

**“Can you fine-tune it on our funds?”**

> **User:** Priya: Can you fine-tune the chatbot so it knows all our fund factsheets?
>
> **Assistant:** That is a knowledge request. Factsheets change monthly and must be cited, so they belong in retrieval, not in the weights.

## Full fine-tuning, and why it is costly

Now suppose you do have a behaviour problem that prompting cannot fix. What does fine-tuning actually involve?

Fine-tuning means continuing to train an already trained model, on a small dataset for your task. You start from its existing weights. In full fine-tuning, every single weight moves. For a seven billion parameter model, that is seven billion numbers changing at every training step.

**Full fine-tuning**

- Keep training a pretrained model on a small, task-specific dataset
- Start from its existing weights, not from scratch
- Full fine-tuning: every weight changes, billions of numbers

Training needs far more memory than running. A common rule of thumb is about sixteen bytes per weight. Two for the weight, two for its gradient, which says which way to nudge it, and about twelve for the optimiser's notes. For seven billion weights, that is about one hundred and twelve gigabytes, before anything else.

**Training memory: about 16 bytes per weight**

| What is stored | Bytes per weight |
|---|---|
| The weight itself (16-bit) | 2 |
| Its gradient: which way to move it | 2 |
| Optimiser memory: master copy + two running averages | 12 |

*7 billion weights x 16 bytes = about 112 GB, before anything else.*

On top of that, you get a complete new copy of the model for every task, and the highest risk of the model forgetting what it already knew. So full fine-tuning is rarely the right first choice outside large labs. In the next video we will see the cheap alternative.

**Full fine-tuning: rarely the first choice**

> **Huge memory. A full new model copy per task.**
> And the highest risk of forgetting what it knew. Mostly done by model providers and large labs.

## Preparing fine-tuning data properly

Whichever method you use, the data matters more than anything else. Let's see how to prepare it.

The usual kind is called supervised fine-tuning, or S F T. Each training example is an input and the ideal answer, like a folder of model answers for a new joiner. Quality beats size. A careful thousand examples usually beat a careless hundred thousand.

**Training on example conversations**

- Each example: an input, and the ideal answer
- Like teaching a new joiner with a folder of model answers
- Quality beats size: 1,000 careful beats 100,000 careless

Six steps. One, define what a good answer is, and build a held-out test set before anything else, just like Day 6. Two, collect inputs that look like real user questions, not easier invented ones. Three, have a domain expert write or approve every target answer.

Four, format every example the same way. Five, remove near duplicates, and make sure no test question sneaks into training. That is a kind of cheating we will meet again in Part 3. Six, include refusals, tool errors, and I don't know answers. If the model never sees them, it will never produce them.

**Six steps, in order**

1. Define the task and build a test set first
2. Collect inputs that look like real questions
3. Have an expert write or approve each answer
4. Format consistently: one example per line
5. Remove duplicates; keep test cases out of training
6. Include refusals, tool errors and “I don't know”

One detail interviewers love. During training, the model is graded only on the assistant's words, the gold blocks. The user's question is fed in as context, but not graded. This is called loss masking. Without it, the model would also learn to write the user's side of the conversation.

**Loss masking: learn only the answer**

> Grey = context only (no learning). Gold = the model is graded on these.
`User:` `Top` `debt` `fund?` `Assistant:` `Deccan` `Bond` `Fund` `.`

A few training settings matter most. The learning rate, meaning how big each nudge to the weights is, must be much smaller than in the original training. Too big, and you damage what the model already knew. And make only one to three passes over the data.

And watch two numbers, not one. The training loss can keep improving while the real answers get worse, because the model is copying the style of the target answers, not their correctness. So always score it on your frozen task test set too.

**The settings that matter most**

- Learning rate: much smaller than original training
- Passes over the data (epochs): usually one to three
- Watch two numbers: training-style loss AND your task test score

*The loss can keep improving while real answers get worse.*

## Catastrophic forgetting

Finally, the biggest risk of fine-tuning, with a dramatic name: catastrophic forgetting.

Train a model hard on one narrow task, and abilities it had before can get worse. Think of a cricketer who practises only sixes for a month, and then forgets how to play a defensive shot. The weights that stored the old skills got moved to fit the new data.

**Catastrophic forgetting**

> **Train hard on one narrow task, and old skills get worse.**
> Like a cricketer who practises only sixes for a month and forgets how to defend.

Four protections. Use methods that keep the original weights frozen, which we cover next. Keep the learning rate low, and make only one to three passes over the data. Mix some general examples into training. And always rerun a general skills test after training, not just your task test.

**Four protections against forgetting**

- Use cheap methods that keep the original weights frozen (next video)
- Low learning rate, only one to three passes over the data
- Mix in some general examples alongside your task data
- Test general skills after training, not just the new task

Quick check. Rahul wants the chatbot to always answer in a strict three line house format. Prompt, retrieval, or fine-tune? Pause and think. The answer: this is behaviour, not knowledge. Try the prompt first. Fine-tune only if the prompt keeps failing on a frozen test set.

**Quick check:** Rahul wants the chatbot to always answer in a strict three-line house format. Prompt, RAG or fine-tune?

<details><summary>Answer</summary>

It is behaviour, not knowledge. Try the prompt first; fine-tune only if it fails on a frozen test set.

</details>

Let's recap. Adapt a model in order: prompt, then retrieval and tools, then fine-tuning. Fine-tuning teaches behaviour, while knowledge belongs in retrieval and tools. Full fine-tuning is expensive. Good data starts with a test set and expert answers. And you guard against forgetting. Next: LoRA, the cheap way to fine-tune, plus distillation and quantization.

- Three levers, in order: prompt, then retrieval and tools, then fine-tune
- Fine-tuning teaches behaviour; knowledge belongs in retrieval and tools
- Full fine-tuning: about 16 bytes per weight, a new model per task
- SFT data: test set first, expert answers, no test leaks, loss masking
- Limit forgetting: frozen base, low learning rate, general tests

The code for this day is in the day seven folder, linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 6, Part 4](day06_p4.md) · [All lessons](README.md) · [Day 7, Part 2](day07_p2.md) →
