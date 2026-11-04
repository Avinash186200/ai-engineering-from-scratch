# Day 1, Part 5: LLM Hallucination, Temperature, Top-p and Choosing a Model

**Watch:** [youtu.be/MPbgfnl12A4](https://youtu.be/MPbgfnl12A4) · **Code:** [`day01_llm_basics/`](../day01_llm_basics/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Why do language models make things up, and what can you do about it? How do temperature and top-p really work? And how do you choose between Claude, GPT, Gemini and open models? The final episode of Day 1.

## What you will learn

- What a hallucination is, why it cannot be fully removed, and six ways to contain it
- Greedy decoding vs sampling
- Temperature and top-p, worked with real numbers
- What settings to use for a factual product
- The model landscape, closed vs open weights, and a 6-point method to choose a model
- Generative models vs embedding models

## Chapters

- [0:00](https://youtu.be/MPbgfnl12A4?t=0) Intro
- [0:22](https://youtu.be/MPbgfnl12A4?t=22) Hallucination
- [1:59](https://youtu.be/MPbgfnl12A4?t=119) Six ways to contain hallucination
- [2:51](https://youtu.be/MPbgfnl12A4?t=171) Sampling, temperature and top-p
- [5:50](https://youtu.be/MPbgfnl12A4?t=350) The model landscape
- [7:17](https://youtu.be/MPbgfnl12A4?t=437) How to choose a model

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we saw how a raw model is trained into an assistant, with fine tuning and preference tuning. In this final part of day one, we cover three practical things: why models make things up, how the next word is actually picked, and how to choose a model.

## Hallucination

First, hallucination. You met the word in part one. Now let's understand it properly.

A hallucination is a confident, fluent statement that is false, or not supported by any source. It follows directly from training. The model learns to produce the most plausible next token. And a plausible, made up number is produced in exactly the same way as a correct one.

**What is a hallucination?**

> **A confident, fluent statement that is false or unsupported**
> A made-up number is produced exactly the same way as a correct one.

Here is an example. Ask a model with no tools: what is the predicted return of Bharat Growth Fund this week? It has never seen our ranking model. But it has seen thousands of sentences like, the predicted return was zero point four something percent. So a fluent answer like zero point four eight percent is a very likely continuation.

It looks right, and it is invented. The real value, from the ranking tool, is zero point five three percent. Nothing inside the model checks facts, and nothing in its training rewarded saying, I don't know.

**Ask a model with no tools**

> **User:** What is the predicted return of Bharat Growth Fund this week?
>
> **Assistant:** Bharat Growth Fund's predicted return this week is approximately 0.48%.
>
> **Tool:** rank_funds → Bharat Growth Fund: +0.53%

Because it comes from the training goal itself, hallucination cannot be removed completely. It is not a bug someone forgot to fix. What we can do is make it rare, and make it visible, through how we design the product.

**It cannot be removed completely**

> **It comes from the training goal itself**
> We can't fix it inside the model. We can make it rare and visible, by design.

Here are six defences. One: tools for anything computed or live, so the model copies numbers instead of inventing them. Two: retrieval with sources, so it answers from passages you supply. Three: instruction rules, such as, never state a number that is not in a tool result, and say so if a tool fails.

Four: low randomness on factual tasks, which we will see in a moment. Five: output checks, where ordinary code verifies that every number in the answer really appears in the tool output. And six: evaluation, a test set that catches problems before release. That is day six.

**Six ways to contain hallucination**

| Defence | How it helps |
|---|---|
| Tools for numbers | The model copies numbers instead of inventing them |
| Retrieval with sources | Answers from supplied passages, and points to them |
| Instruction rules | “Never state a number that is not in a tool result” |
| Low randomness | Less creative drift on factual tasks |
| Output checks | Code checks every number appears in the tool output |
| Evaluation | A test set catches problems before release (Day 6) |

## Sampling: how the next word is picked

Defence number four needs some explaining. The model gives a probability for every token. But which one actually gets written?

There are two ways. Greedy decoding always picks the most likely token. Same input, same answer every time, but it can get repetitive. Sampling picks at random, according to the probabilities. Like a lucky draw where Bharat has forty four tickets and Nifty has twenty seven. That gives more varied, natural text.

**Greedy vs sampling**

- **Greedy**
  - Always pick the most likely token
  - Same answer every time
  - Can get repetitive
- **Sampling**
  - Draw at random, by the probabilities
  - Varied, more natural text
  - Like a weighted lucky draw

The main setting that controls sampling is called temperature, written T. Before the softmax, every raw score is divided by T. A temperature below one sharpens the odds, so the top token dominates. Above one flattens them, so unlikely tokens get more chances.

**Temperature reshapes the odds**

- Divide every raw score by T, then softmax
- T below 1: sharper, the top token dominates
- T above 1: flatter, unlikely tokens get more chances

Let's see real numbers. The model is completing, the top fund is, and has four candidates with raw scores two, one point five, one point two, and zero point five. At temperature one, a normal softmax gives Bharat forty four percent. At temperature zero point five, Bharat jumps to sixty two percent. At temperature two, it drops to thirty four. And as temperature goes to zero, it becomes greedy: always Bharat.

**“The top fund is …”: four candidates**

| Token | Score | T = 0.5 | T = 1 | T = 2 |
|---|---|---|---|---|
| Bharat | 2.0 | 0.62 | 0.44 | 0.34 |
| Nifty | 1.5 | 0.23 | 0.27 | 0.27 |
| Deccan | 1.2 | 0.12 | 0.20 | 0.23 |
| a | 0.5 | 0.03 | 0.10 | 0.16 |

*T = 1: e^2.0 = 7.39; total of all four = 16.84; 7.39 ÷ 16.84 = 0.44*

The second setting is called top p. It keeps only the smallest group of top tokens whose probabilities add up to at least p, and samples from those. With p of zero point seven: Bharat plus Nifty gives zero point seven one. That is enough, so only those two can be chosen. The long tail of unlikely tokens is cut off.

**Cut off the long tail**

> Top-p = 0.7, using the T = 1 odds
- Bharat: 0.44
- Nifty: 0.27
- Deccan: 0.20
- a: 0.10

*0.44 + 0.27 = 0.71 ≥ 0.7, so only Bharat and Nifty can be picked.*

You can check these numbers yourself. Open sampling demo dot py. It divides the scores by the temperature, applies softmax, and prints the odds. Run it, then try your own temperatures and watch the odds sharpen and flatten.

**Temperature in eight lines**

`day01_llm_basics/sampling_demo.py`
```python
import numpy as np

tokens = ["Bharat", "Nifty", "Deccan", "a"]
scores = np.array([2.0, 1.5, 1.2, 0.5])

for T in [0.5, 1.0, 2.0]:
    p = np.exp(scores / T)
    p = p / p.sum()                      # softmax
    print(f"T={T}:", dict(zip(tokens, p.round(2))))
```

*Run: python day01_llm_basics/sampling_demo.py*

So what should you use? For tool calls, numbers and extraction, keep temperature low, so the same question gives the same tool call every time. For explanations, low to moderate. For brainstorming or marketing copy, go higher. Some of the newest models fix these settings and give you a thinking setting instead. The principle stays: for factual work, be consistent, not creative.

**Settings for a real product**

| Task | Setting | Why |
|---|---|---|
| Tool calls, numbers, extraction | Low (0–0.2) | Same question, same call |
| Explanations for analysts | Low to moderate | Consistent wording |
| Brainstorming, marketing copy | Higher (0.7–1.0) | Variety is the goal |

*Some newest models fix sampling and offer a thinking/effort setting instead.*

## The model landscape

Finally, which model should you actually use?

Here are the main families. Claude from Anthropic, GPT from OpenAI, and Gemini from Google, all reached through a paid API. And open weight families like Llama, Mistral, Qwen and DeepSeek, which you can download and run yourself. Under the hood, they are all the same kind of machine: decoder only transformers, trained in the stages we saw last video.

**Who makes the models**

| Family | Maker | Access |
|---|---|---|
| Claude | Anthropic | Paid API |
| GPT | OpenAI | Paid API |
| Gemini | Google | Paid API |
| Llama, Mistral, Qwen, DeepSeek | Various | Open weights |

*All are decoder-only transformers, trained in the stages from Part 4.*

The key choice is closed versus open. A closed API model is usually the best in quality, and there is nothing to run: you just call a web address and pay per token. An open weight model is close behind, but you run the servers yourself. In return, your data never leaves your building, and at very high volume it can be cheaper.

**Closed API vs open weights**

|  | Closed API | Open weights |
|---|---|---|
| Quality | Usually the frontier | Close behind |
| Running it | Nothing: call a web address | You run the GPU servers |
| Cost | Pay per token | Pay for hardware |
| Your data | Goes to the provider | Stays with you |

One warning. Rankings change every few months. So never hard wire one provider into your code. In the real product I built, the model sat behind a thin adapter, one simple interface, so switching providers was a setting, not a rewrite. We build one on day eight.

**Rankings change every few months**

> **Never hard-wire one provider into your code**
> Put the model behind a thin adapter, so switching is a setting, not a rewrite (Day 8).

When an interviewer asks, which model would you use, never answer with a brand. Answer with a method. One: quality on your own test questions, not public leaderboards. Two: cost per finished task, not per call. A cheaper model that needs three retries can cost more.

Three: speed. How long until the first word appears, and the total time, compared to what your users will tolerate. Four: the context length you need for your documents and conversations.

Five: data rules. Is the client's data allowed to leave the country, or go to this provider? And six: risk. Rate limits, uptime, and when the provider will retire the model. Six points, and you sound like an engineer, not a fan.

**How to choose a model**

1. Quality on YOUR test questions, not public leaderboards
2. Cost per finished task, not per call
3. Speed: time to first word, and total time
4. Context length you need
5. Data rules: where data may go; can it be stored?
6. Risk: rate limits, uptime, model retirement dates

Last idea. Most AI products use two different kinds of model. A generative model writes text: that is the chat model. An embedding model turns a whole piece of text into one list of numbers, so that similar texts get similar numbers. It powers search. They are chosen, priced and tested separately. Our chatbot will use both by day five.

**Generative vs embedding models**

- **Generative model**
  - Writes text
  - The chat model in our chatbot
  - Decoder-only
- **Embedding model**
  - Turns text into one list of numbers
  - Powers search: similar text, similar numbers
  - Often encoder-only

*Chosen, priced and tested separately. We use both by Day 5.*

Quick check. Pause and answer: at temperature zero point five, what happens to the chance of the most likely token? And at temperature two? At zero point five, it goes up, from forty four to sixty two percent in our example. At two, it goes down, to thirty four. Low temperature means consistent.

**Quick check:** At temperature 0.5, what happens to the chance of the most likely token? And at 2?

<details><summary>Answer</summary>

At 0.5 it rises (0.44 → 0.62 in our example). At 2 it falls (to 0.34). Low T = consistent.

</details>

Let's recap day one's final part. Hallucination comes from the training goal, so we contain it by design: numbers from tools, facts from retrieval, rules in the instructions. Temperature sharpens or flattens the odds, and top p cuts the tail. Choose models by method, not brand. That completes day one. Next, day two: prompts, structured output, and safety.

- Hallucination comes from the training goal; contain it by design
- Numbers from tools, facts from retrieval, rules in the instructions
- Temperature sharpens or flattens odds; top-p cuts the tail
- Choose models by your own tests, cost per task, speed, data rules
- Generative models write; embedding models power search

The code for this video is linked in the description. Try the sampling demo, subscribe, and I will see you on day two.

---

← [Day 1, Part 4](day01_p4.md) · [All lessons](README.md) · [Day 2, Part 1](day02_p1.md) →
