# Day 1, Part 2: Tokens, Context Windows and LLM Pricing Explained

**Watch:** [youtu.be/XwUcZ_uaJBY](https://youtu.be/XwUcZ_uaJBY) · **Code:** [`day01_llm_basics/`](../day01_llm_basics/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Everything in the LLM world is measured in tokens: what the model reads, what it writes, how much it remembers, and what you pay. This episode explains tokens from scratch.

## What you will learn

- What a token is, and why models use word pieces instead of words or letters
- How a tokenizer is built (Byte-Pair Encoding) with a tiny worked example
- Why numbers and fund names split into odd pieces, and why that matters
- The context window, and the "lost in the middle" problem
- How to price one chatbot question in dollars and rupees (illustrative numbers)

## Chapters

- [0:00](https://youtu.be/XwUcZ_uaJBY?t=0) Intro
- [0:41](https://youtu.be/XwUcZ_uaJBY?t=41) What is a token?
- [2:15](https://youtu.be/XwUcZ_uaJBY?t=135) How a tokenizer is built (BPE)
- [3:50](https://youtu.be/XwUcZ_uaJBY?t=230) Why numbers split into pieces
- [5:15](https://youtu.be/XwUcZ_uaJBY?t=315) The context window
- [7:00](https://youtu.be/XwUcZ_uaJBY?t=420) Pricing one question in $ and ₹

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last video, we saw that a large language model is a classifier that predicts the next token, one at a time. Today, we open that word up. What exactly is a token, and why is everything, from memory to price, measured in them?

We will answer three questions. What a token is. How much text a model can hold at once, which is called the context window. And what one question to our research assistant chatbot actually costs, in dollars and in rupees.

**Three questions**

- What is a token, and why not just use words?
- How much text can a model read at once?
- What does one chatbot question actually cost?

## What is a token?

Let's start with the word token itself.

A token is simply a small piece of text. Think of it like the pieces of a jigsaw puzzle. Sometimes one piece is a whole word. Sometimes it is part of a word, a chunk of a number, or a single symbol like a comma.

Remember, the model is a classifier, and a classifier needs a fixed list of categories. That fixed list of tokens is called the vocabulary. It usually has somewhere between fifty thousand and two hundred thousand entries.

**A token is a piece of text**

> **The model has a fixed list of tokens: its vocabulary**
> Typically 50,000 to 200,000 tokens. Every text must be cut into these pieces.

Why pieces, and not just letters or whole words? Look at the options. If every letter is a token, the list is tiny, but a single page becomes thousands of tokens. Everything gets slow and expensive.

If every whole word is a token, the list needs millions of entries, and it still breaks. A new fund name, a typo, or a word like UPI that it never saw, and the model has no category for it.

Word pieces are the compromise. Common words get their own token, and rare words are built from smaller pieces. So nothing is ever unknown. Every modern language model works this way.

**Three ways to cut up text**

| Unit | List size | Problem |
|---|---|---|
| Letters | ~100–300 | Texts become very long: slow and costly |
| Whole words | Millions | Every new name, typo or product is unknown |
| Word pieces | 50k–200k | The compromise every modern LLM uses |

*Any text can be built from pieces, so nothing is ever “unknown”.*

## How a tokenizer is built

The program that cuts text into tokens is called a tokenizer. How does it decide where to cut?

Most tokenizers use a method called Byte Pair Encoding, or B P E. Imagine a tiny collection of text with the words lower, lowest and newer, repeated many times. At the start, every single letter is its own symbol.

Now count which two neighbouring symbols appear together most often. Here, w followed by e. Merge them into one new symbol, w e.

Repeat. The next most common pair gets merged, then the next, again and again. It is like how we shorten common phrases in chat messages, because we type them so often.

Stop when the list reaches the target size. Now common words are a single token, and rare words split into familiar pieces. The tokenizer is built once and then frozen. Every provider has its own, so the same sentence can give different counts on different models.

**Merge the most common pairs**

1. Start: every letter is a symbol: l o w e r, l o w e s t, n e w e r
2. Most frequent pair: “w e” → merge into one symbol “we”
3. Keep merging: “we r” → “wer”, “l o” → “lo”, and so on
4. Stop at the target size: common words become one token

*Built once, then frozen. Every text sent to the model is cut this way.*

Two rules of thumb to remember. For English, one token is about four characters. And a hundred words is roughly a hundred and thirty tokens. Names, numbers and code take more tokens than ordinary words.

**How many tokens is my text?**

> **100 English words ≈ 130 tokens**
> One token ≈ 4 characters, or about three-quarters of a word. Names, numbers and code use more.

## Why numbers look strange to a model

That last point has a big consequence for our fund chatbot.

Here is an illustrative split. A word like Deccan is not common in English text, so it may be cut into two pieces, dec and can. Common words like bond and fund are one token each, often including the space in front.

Now look at the number. One hundred and three point zero three one might become three pieces: one zero three, a dot, and zero three one. The model never sees it as a quantity. It sees three bits of text.

**A fund name becomes pieces**

> “Deccan Bond Fund returned 103.031”
`Dec` `can` ` Bond` ` Fund` ` returned` ` 103` `.` `031`

*The model never sees 103.031 as a quantity, only as three text pieces.*

So this is a second, very mechanical reason why language models are unreliable at arithmetic, and even at copying long numbers exactly. And it is a second reason our design rule holds: numbers come from tools, not from the model.

**Why numbers look strange to a model**

> **A second reason numbers must come from tools**
> Arbitrary number chunks make arithmetic and copying long numbers unreliable.

You can see this yourself. Open tokens demo dot py from the day one folder. It uses a free, open tokenizer, cuts three sentences into tokens, and prints each piece. Run it, and notice how the rupee amount and the fund name split.

**Count tokens in Python**

`day01_llm_basics/tokens_demo.py`
```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

for text in ["Which funds look best this week?",
             "Deccan Bond Fund returned 103.031",
             "Priya paid ₹1,250 via UPI"]:
    ids = enc.encode(text)
    pieces = [enc.decode([i]) for i in ids]
    print(len(ids), pieces)
```

*Run: python day01_llm_basics/tokens_demo.py*

## The context window

Next: how much text can a model look at in one go?

The context window is the maximum number of tokens the model can handle in one call. Think of it as the size of the model's desk. Everything must fit on the desk at once: what you send, and the answer it writes back.

What you send includes more than the question. There are the instructions, called the system prompt. The chat history. Any documents. And the results that tools return. It all takes space on the desk.

**The context window**

- Maximum tokens the model can handle in one call
- Counts what you send AND what it writes back
- You send: instructions, chat history, documents, tool results

Windows have grown fast. Older models handled around eight thousand tokens. Models in twenty twenty four handled up to two hundred thousand. Current frontier models offer up to about a million. If your request is bigger than the window, it is rejected, or you must trim it.

**Context windows have grown fast**

- Current frontier: 1,000,000
- 2024 models: 200,000
- Older models: 8,000

*Too big for the window? The request is rejected or must be trimmed.*

But a bigger desk does not mean you should pile everything on it. Researchers have repeatedly found a problem called lost in the middle. Models remember the start and the end of a long prompt well, but miss things buried in the middle. Like a student who only revises the first and last chapters.

**Lost in the middle**

> **Models recall the start and end of a long prompt best**
> Facts buried in the middle are more easily missed. Long prompts also cost more and run slower.

The fix is to send only what matters. Find the five most relevant paragraphs and send those, not the whole library. That technique is called retrieval, and we will build it ourselves on day five.

**Send the right pages, not the library**

> **Send the 5 most relevant paragraphs, not 500 pages**
> This is called retrieval. We build it on Day 5.

## Why everything is priced in tokens

Finally, money. Every provider charges by the token.

You pay separately for input tokens and output tokens, quoted per million. Remember from part one: input is read in one fast pass, but every output token needs its own pass. So output costs several times more. For our example, we will use illustrative prices: three dollars per million in, fifteen dollars per million out.

**Input tokens and output tokens**

- **Input tokens**
  - Everything you send
  - Read in one fast pass
  - Cheaper per token
- **Output tokens**
  - Everything the model writes
  - One model pass per token
  - Several times more expensive

*Prices are quoted per million tokens. Illustrative: $3 in, $15 out.*

Let's price one question to our research assistant. The fixed instructions and the descriptions of its tools: two thousand tokens. The conversation so far: one thousand. And the fund ranking that the tool returned: fifteen hundred.

That is four thousand five hundred input tokens, which costs about one point three five cents. The answer is three hundred output tokens, about zero point four five cents. Notice the answer is tiny, yet it costs a third as much as all the input.

**One chatbot question, token by token**

| What is sent or written | Tokens |
|---|---|
| System prompt + tool descriptions | 2,000 |
| Conversation so far | 1,000 |
| Tool result (fund ranking as JSON) | 1,500 |
| Input total | 4,500 |
| The model's answer (output) | 300 |

*Input: 4,500 × $3 ÷ 1M = $0.0135.   Output: 300 × $15 ÷ 1M = $0.0045.*

Add them up: about one point eight cents per question. At an illustrative eighty five rupees to the dollar, that is about one rupee fifty paise. A thousand questions a day is around fifteen hundred rupees a day. Cheaper than a cup of chai per question, but it adds up fast at scale.

**What it costs in rupees**

> **≈ $0.018 ≈ ₹1.5 per question**
> At ₹85 per dollar. 1,000 questions a day ≈ $18 ≈ ₹1,530 a day. Real prices vary by model.

Two levers follow immediately. First, make tools return only what the model needs, say the top five funds, not every fund in the market. Second, the fixed instructions are the same every time, so providers let you cache them, billed at a fraction of the price. We cover that on day two.

**Two levers to cut the bill**

- Send only what the model needs: the top 5 funds, not all of them
- Reuse the fixed instructions with prompt caching (Day 2)

Quick check. Pause and answer: our answer is only three hundred tokens, while the input is four and a half thousand. Why does the answer still cost a third as much? Because output tokens are priced several times higher, since each one needs its own pass through the model.

**Quick check:** Our chatbot's answer is 300 tokens and its input is 4,500. Why can the answer still cost a third as much?

<details><summary>Answer</summary>

Output tokens cost several times more, because each one needs its own pass through the model.

</details>

Let's recap. A token is a word piece, and models classify over tens of thousands of them. Tokenizers are built by merging frequent pairs. Numbers split into chunks, which is another reason they come from tools. The context window holds everything, and the middle gets lost. And you pay per token, with output costing more. Next video, we go inside the transformer itself.

- A token is a word piece; models classify over 50k–200k of them
- Tokenizers merge frequent letter pairs (BPE); 100 words ≈ 130 tokens
- Numbers split into chunks: another reason they come from tools
- The context window holds input + output; the middle gets lost
- You pay per token; output costs more. Send less, cache the rest

The code for this video is linked in the description. Try the tokens demo, and I will see you in the next video.

---

← [Day 1, Part 1](day01_p1.md) · [All lessons](README.md) · [Day 1, Part 3](day01_p3.md) →
