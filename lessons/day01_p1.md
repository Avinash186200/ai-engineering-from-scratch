# Day 1, Part 1: What is a Large Language Model? (No ML Background Needed)

**Watch:** [youtu.be/uXoD4kXr1YY](https://youtu.be/uXoD4kXr1YY) · **Code:** [`day01_llm_basics/`](../day01_llm_basics/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

What actually is a large language model? In this first episode of AI Engineering from Scratch, we strip away the hype: an LLM is a classifier that predicts the next word, trained on labels the text gives for free.

## What you will learn

- Why an LLM is "just" a classifier with ~100,000 classes
- Self-supervised learning: where the training labels come from
- Why predicting words creates knowledge and reasoning
- How text generation works, one token at a time
- What an LLM is NOT, and the design rule every real AI product follows

## Chapters

- [0:00](https://youtu.be/uXoD4kXr1YY?t=0) Intro
- [1:13](https://youtu.be/uXoD4kXr1YY?t=73) The project we will build
- [1:53](https://youtu.be/uXoD4kXr1YY?t=113) An LLM is a classifier
- [2:48](https://youtu.be/uXoD4kXr1YY?t=168) Where the training data comes from
- [4:19](https://youtu.be/uXoD4kXr1YY?t=259) Why predicting words creates knowledge
- [5:06](https://youtu.be/uXoD4kXr1YY?t=306) Writing = predicting, one word at a time
- [5:45](https://youtu.be/uXoD4kXr1YY?t=345) What an LLM is not
- [6:26](https://youtu.be/uXoD4kXr1YY?t=386) The design rule for real products

## Lesson notes

Slide content and the full narration, in order.

Hi, I am Avinash, and welcome to AI Engineering from Scratch. In this first video, we answer one question: what is a large language model, really? You do not need any machine learning background to follow along.

One quick tip before we start: these videos are paced for learning, so if it feels slow, watch at one point two five times speed.

First, a quick look at where this series is going. The goal is simple: take you from zero to building real AI products, the kind companies are hiring for right now. Every day has short videos, and code you can run yourself.

**What this series covers**

- Go from zero to building real AI products
- 10 days, short videos, with code you can run
- We build one real project across the whole series

We start with how language models work. Then how to talk to them safely, how to build agents that use tools, how to connect them to your own documents, how to test them, how to put them into production, and finally, system design and mock interviews. This video is the very first step.

Throughout the series, we will build one real project: a research assistant chatbot. An analyst types a question in plain English, like, which funds look best this week?

And gets back a clear answer, built on real numbers from a model, not a guess.

**The project: a research assistant chatbot**

> **User:** Which funds look best this week?
>
> **Assistant:** Top 3 by predicted return: 1. Bharat Growth Fund +0.53%  2. Nifty Value Fund +0.51%  3. Deccan Bond Fund +0.49%. Ranked by a model, not a guess.

I built a system like this at work for investment analysts, so everything you see comes from a real product. In this series, we rebuild it from scratch, with public data and open code that you can download and run.

**Built from a real product**

- I built a system like this at work for investment analysts
- Analysts ask in plain English; answers come from real models and data
- In this series we rebuild it from scratch, with public data and open code

## An LLM is a classifier

Now, what is a large language model? Strip away the hype, and it is a classification model.

A classifier simply sorts an input into categories, like an email filter deciding spam or not spam. Here, the input is some text, for example, the capital of India is, blank. And the output is a probability for every possible next word. New Delhi gets ninety one percent. Mumbai, four percent. And so on, for every word it knows.

**An LLM is a classifier**

> The capital of India is  ____
- New Delhi: 0.91
- Mumbai: 0.04
- the: 0.02
- a: 0.01

So it is a classifier. The only unusual thing is the number of categories: roughly a hundred thousand, one for each word piece it knows. We call those word pieces tokens.

**An LLM is a classifier**

> **A classifier with ~100,000 classes**
> One class per token: the word pieces the model knows.

Where do the labels come from? This is the clever part. Take any sentence, say, Rohit Sharma hit a six over long on. Slide along it. At each position, the input is everything so far, and the label is the word that actually came next.

One sentence gives you many labelled examples, with no human labelling at all. This is called self supervised learning. Feed it trillions of words, and you get trillions of training examples.

**Free training data: self-supervised**

| Input: everything so far | Label: next word |
|---|---|
| Rohit | Sharma |
| Rohit Sharma | hit |
| Rohit Sharma hit | a |
| Rohit Sharma hit a | six |
| Rohit Sharma hit a six over long | on |

*1 sentence = many labelled examples. No humans labelling.*

A short note if you have done some machine learning before. If not, don't worry, just listen along. In machine learning terms, the input features are the text so far, and the label is the next token.

The final layer of an LLM is the same maths as multinomial logistic regression: a softmax, which turns scores into probabilities that add up to one. And it is trained with log loss: the model is penalised when it gives a low probability to the word that actually came next.

The big difference from classic machine learning: nobody designs the input features by hand. The network learns its own understanding of the text.

**The same ideas you may already know**

| Classic machine learning | The LLM version |
|---|---|
| Input features X | The text so far |
| Label y | The next token |
| Softmax / logistic regression | The LLM's final layer |
| Log loss | The LLM's training loss |
| Hand-built features | Learned automatically |

## Why predicting words creates knowledge

Now the surprising part. Why does predicting the next word produce something that seems to know things?

Because to predict well across all the text on the internet, the model is forced to learn whatever makes the next word predictable. To finish a fact, it has to store the fact. To finish a line of code, it has to learn the programming language.

To finish the last line of a worked maths problem, it has to reproduce the reasoning that leads there.

**Why predicting words creates knowledge**

- To finish “The capital of India is …” it must store the fact: New Delhi
- To finish a line of Python, it must have learned Python
- To finish a worked maths answer, it must follow the reasoning steps

Nobody programs these abilities. They emerge, because they reduce the loss. That is why scale matters so much.

**Why predicting words creates knowledge**

> **Nobody programs these abilities.**
> They emerge, because they make the next word easier to predict. That is why scale matters.

## Writing = predicting, one word at a time

So how does it write a whole paragraph? It never does. It only ever predicts one token.

To generate text, it runs in a loop. Read the text so far, score every possible next word, pick one, add it to the text, and repeat.

Each gold block here is one more trip around the loop. One consequence you will meet in every project: output tokens are slower and more expensive than input tokens, because each new token needs its own pass through the model.

**Writing = predicting, one word at a time**

> Loop: read the text so far → score every next word → pick one → add it → repeat
`The` `top` `fund` `is` `Bharat` `Growth` `Fund` `.`

*Output tokens are slower and cost more than input: one model pass per new token.*

## What an LLM is not

It is just as important to know what an LLM is not.

It is not a database. It does not look facts up.

It is not a calculator. To the model, a number is just a few pieces of text.

And it is not aware of truth. It is trained to produce plausible text, not true text. Put those together, and you get its signature failure: a fluent, confident, wrong answer. That is called a hallucination, and we will spend a whole video on it.

**What an LLM is not**

- Not a database: it reproduces patterns, it doesn't look facts up
- Not a calculator: numbers are just text pieces to it
- Not aware of truth: it is trained on plausible, not true

*Result: a fluent, confident, wrong answer. That is a hallucination.*

## The design rule for real products

So how do we build a reliable product on top of something that can invent answers?

First, understand that a product like our chatbot has two kinds of parts. The LLM understands and writes language, like a smart colleague who can read and explain. But it does not know today's fund numbers.

The second part is a tool. A tool is just a normal program the LLM is allowed to call: a ranking model, a calculator, or a database. Tools give exact, up to date answers. The LLM decides which tool to call. The tool does the actual work.

**The LLM and its tools**

- **The LLM**
  - Understands and writes language
  - Like a smart colleague who can read and explain
  - Does not know today's fund numbers
- **A tool**
  - A normal program the LLM can call
  - e.g. a ranking model, a calculator, a database
  - Gives exact, up-to-date answers

*The LLM decides WHICH tool to call. The tool does the actual work.*

Now watch them work together in our research assistant. An analyst asks, which funds look best this week? The LLM reads the question and decides it needs the ranking tool.

The ranking tool, a separate model trained on fund data, computes the actual numbers. Then the LLM explains the result in plain language. The model ranks. The LLM explains. Numbers always come from tools, never from the LLM's memory. If you remember one thing from this video, remember that.

**The design rule for real products**

**Analyst asks** (“Which funds look best this week?”) → **LLM** (understands, picks the ranking tool) → **Ranking tool** (a model trained on fund data computes the numbers) → **LLM** (explains the result in plain language)

*The model ranks. The LLM explains.*

*Numbers always come from tools, never from the LLM's memory.*

Quick check. Pause the video and answer: why should a fund chatbot never let the LLM state a return figure from its own memory? The answer: because an LLM predicts plausible text, so it can invent a confident, wrong number. Numbers must come from a tool.

**Quick check:** Why should a fund chatbot never let the LLM state a return figure from memory?

<details><summary>Answer</summary>

An LLM predicts plausible text, so it can invent a confident, wrong number. Numbers must come from a tool.

</details>

Let's recap. An LLM is a next token classifier with around a hundred thousand classes. Its training labels come free from the text itself. Knowledge emerges because it makes prediction easier. It writes one token at a time. And because it is not a database or a calculator, real products give it tools. In the next video, we open the box: tokens, and why everything in this world is priced in them.

- An LLM is a next-token classifier with ~100k classes
- Training labels come free from the text itself
- Knowledge emerges because it makes prediction easier
- It writes one token at a time; output costs more than input
- It is not a database or calculator: real products give it tools

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next video.

---

[All lessons](README.md) · [Day 1, Part 2](day01_p2.md) →
