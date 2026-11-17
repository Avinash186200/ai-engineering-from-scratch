# LLM fundamentals

Code to back these answers: `day01_llm_basics/`, `day02_prompting/`.

### 1. How does an LLM produce an answer?
It splits the text into tokens, turns them into vectors, runs them through transformer layers where attention
mixes in context, and outputs a probability for every token in its vocabulary. One token is sampled, appended, and
the same model runs again. It repeats until an end token or the length limit.

### 2. How is that like classical ML?
At each step it is a classifier with about 100,000 classes, trained with cross-entropy and gradient descent. The
differences are scale, self-supervised labels (the next word in real text), and that it is applied over and over to
its own output.

### 3. Why can't it do exact arithmetic or know today's data?
It predicts likely text, it does not calculate, and its knowledge stops at the training cut-off. So you give it a
calculator or a data tool, and you put fresh facts into the prompt through retrieval.

### 4. What is a token, and why should you care?
A piece of text, often part of a word. Cost, latency and the context limit are all counted in tokens, and odd
tokenisation explains some failures, like miscounting letters.

### 5. 2,000 input and 500 output tokens at 3 and 15 per million. What does a call cost? Why is output dearer?
2,000 x 3 / 1e6 = 0.006 plus 500 x 15 / 1e6 = 0.0075, so 0.0135. Output is dearer because tokens are generated one
at a time, each needing a full pass, while input is processed in parallel.

### 6. Same question, different answers. Why, and how do you fix it?
Sampling is random. Lower the temperature, fix the prompt and the model version, and for anything factual make
the answer come from a tool or retrieved text so the wording can vary but the facts cannot.

### 7. What temperature for extraction versus brainstorming?
Near zero for extraction, classification and tool calls. Higher, around 0.7 to 1, for ideas and drafts.

### 8. Why do LLMs hallucinate?
They are trained to produce fluent, likely text, not to say "I don't know". When the answer is not in the prompt or
well learned, a plausible guess comes out. Ground answers in sources and allow an explicit "not found".

### 9. What is the context window, and what happens if you exceed it?
The maximum tokens the model can see at once, input and output together. Past it the API errors or you must cut
text. Quality also drops before the limit when the key fact sits in the middle of a long prompt.

### 10. What goes into an LLM API call?
Model name, system prompt, the message history, tool definitions, settings such as temperature and max tokens,
and sometimes a response format. Back come the content, any tool calls, a stop reason and token usage.

### 11. Big model or small model?
Start with a strong model to learn what good looks like, build the eval set, then try smaller models per task and
keep the cheapest one that passes. Route only the hard requests to the big model.

### 12. What are embeddings?
Vectors where similar meanings sit close together. Used for semantic search, clustering and deduplication.

### 13. What is attention, simply?
Each token decides how much to look at every other token and pulls in information from the relevant ones. Its cost
grows with the square of the length, which is why long context is expensive.

### 14. What goes into a system prompt?
Role and audience, what it may and may not do, how to use tools, the output format, how to treat untrusted text,
and what to say when it does not know. Keep it versioned and tested like code.

### 15. What is structured output, and why use it?
Forcing the reply into a schema, usually JSON, validated by code. Downstream code can rely on it, and you retry or
fail cleanly when validation fails.

### 16. Few-shot prompting and chain of thought?
Few-shot means showing a few examples of input and ideal output. Chain of thought means letting the model reason
step by step before answering. Both raise quality on harder tasks and both cost tokens.

### 17. What is prompt injection, and how do you defend?
Text from a user, document or tool result that tries to override your instructions. Mark untrusted text as data,
give tools the least privilege, check actions in code outside the model, and test with attack cases.

### 18. What is prompt caching?
The provider reuses the processed form of a repeated prompt prefix, which cuts cost and latency. Put stable parts
first (system prompt, tool definitions, long documents) and the changing question last.
