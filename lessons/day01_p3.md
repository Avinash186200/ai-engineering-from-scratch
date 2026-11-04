# Day 1, Part 3: How Transformers Work: Attention Explained Simply, with Numbers

**Watch:** [youtu.be/qAVZStJKK1I](https://youtu.be/qAVZStJKK1I) · **Code:** [`day01_llm_basics/`](../day01_llm_basics/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

What happens inside a large language model between your question and its next word? This episode walks through the transformer step by step, for complete beginners.

## What you will learn

- Embeddings: how words become lists of numbers, and why similar words end up close
- Attention, with a fully worked "river bank" example
- The feed-forward layer, residual connections and normalisation
- The final softmax that produces next-word probabilities
- Decoder-only vs encoder-only models, and where each is used

## Chapters

- [0:00](https://youtu.be/qAVZStJKK1I?t=0) Intro
- [0:19](https://youtu.be/qAVZStJKK1I?t=19) The big picture
- [1:04](https://youtu.be/qAVZStJKK1I?t=64) Embeddings: words become numbers
- [3:14](https://youtu.be/qAVZStJKK1I?t=194) Attention, with the river bank example
- [6:57](https://youtu.be/qAVZStJKK1I?t=417) Feed-forward, residuals, normalisation
- [8:40](https://youtu.be/qAVZStJKK1I?t=520) Decoder-only vs encoder-only

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we learned that models read and write tokens, and that everything is priced in them. Today, we look inside the machine. What happens between the tokens going in and the next word coming out?

The machine inside every modern language model is called a transformer. Here is one trip through it. First, the text is cut into tokens, and each token becomes an id number. Then each id is turned into a list of numbers, called an embedding.

Then those numbers pass through a stack of layers, dozens of them, each with two parts: attention, and a feed forward network. Finally, a softmax turns the result into a probability for every possible next token. Four ideas. Let's take them one at a time.

**One trip through the model**

**Text → tokens** (cut into word pieces, then ids) → **Embeddings** (each id becomes a list of numbers) → **Layers × N** (attention + feed-forward, repeated) → **Softmax** (a probability for every next token)

*Four ideas. We take them one at a time.*

*Built on one 2017 research paper: “Attention Is All You Need”.*

## Embeddings: words become numbers

Step one. A computer cannot do maths on words. So how do words become numbers?

After tokenising, the text is just a list of id numbers. But those ids are only labels, like roll numbers in a class. Roll number forty is not bigger than roll number four in any useful way. So the model uses a big lookup table, with one row per token, that swaps each id for a list of numbers.

That list is called an embedding, and in real models it is thousands of numbers long. Nobody types these numbers in. They start random, and are learned during training, along with everything else.

**Each token gets a list of numbers**

- After tokenising, text is just ids: [791, 33417, 1963]
- Ids are only labels, like roll numbers in a class
- A big lookup table swaps each id for a learned list of numbers
- Real lists are thousands of numbers long; they are learned, not typed in

Here is a toy example with just three numbers each. Fund, scheme, and cricket. Because the numbers are learned from how words are used, words used in similar sentences end up with similar lists. Fund and scheme look alike. Cricket looks very different.

**Similar words end up close**

| Word | Toy embedding |
|---|---|
| fund | [0.90, 0.10, 0.30] |
| scheme | [0.85, 0.15, 0.25] |
| cricket | [0.10, 0.90, 0.20] |

We measure closeness with cosine similarity. Think of each list as an arrow. If two arrows point the same way, the score is one. If they are unrelated, it is near zero. Fund and scheme score zero point nine nine seven. Fund and cricket, only zero point two seven. Remember this, we will use it for search on day five.

**Measuring closeness: cosine similarity**

> **fund vs scheme ≈ 0.997
fund vs cricket ≈ 0.27**
> Cosine similarity: 1 means same direction, 0 means unrelated. We use this again on Day 5.

One detail. Priya paid Rahul, and Rahul paid Priya, use the same words, but mean very different things for Rahul's UPI balance. The next step, attention, ignores word order by itself. So the model adds each token's position, first, second, third, into its numbers.

**Position matters**

> **“Priya paid Rahul” ≠ “Rahul paid Priya”**
> The next step ignores word order, so each token's position is added to its numbers.

## Attention: words borrow meaning

Step two is the heart of the transformer: attention.

The problem: the meaning of a word depends on the words around it. Bank, after river, is the edge of a river. Bank, after investment, is a financial company. So each word needs a way to look at its neighbours, and borrow meaning from the ones that matter.

**One word, two meanings**

- **The river bank**
  - The edge of a river
  - Water, mud, fishing
- **The investment bank**
  - A financial company
  - Deals, money, offices

*Meaning depends on the neighbours. Attention lets each word look at them.*

Think of a library. For every token, the model makes three new lists of numbers. The first is the query: what am I looking for? Like the question you bring to the librarian.

The second is the key: what do I contain? Like the label on the spine of each book, so others can find it.

The third is the value: what information do I hand over if someone picks me? Like the contents of the book. All three are made by multiplying the token's embedding by tables of weights that the model learned.

**Query, key and value**

- Query: “what am I looking for?”
- Key: “what do I contain?”
- Value: “what do I pass on?”

*Each comes from multiplying the embedding by a learned table of weights.*

Now a worked example. The sentence is, the river bank. We compute attention for the token bank. First, compare bank's query with each token's key. That gives a score: the gets zero point one, river gets two point zero, and bank itself gets zero point five. Higher means more relevant.

Next, softmax, which turns scores into weights that add up to one. Raise e to the power of each score, add them up to get ten point one four, and divide each by the total. The gets eleven percent. River gets seventy three percent. Bank gets sixteen percent.

**“The river bank”: attention for bank**

| Token | Score | e^score | Weight |
|---|---|---|---|
| The | 0.1 | 1.105 | 0.11 |
| river | 2.0 | 7.389 | 0.73 |
| bank | 0.5 | 1.649 | 0.16 |

*Softmax: 1.105 + 7.389 + 1.649 = 10.143.   River: 7.389 ÷ 10.143 = 0.73*

Finally, the new bank is a weighted blend of the three tokens' values. Seventy three percent of it now comes from river. So bank has been pulled towards the riverside meaning. Nobody wrote a rule saying river changes bank. The model learned it.

**“The river bank”: attention for bank**

> **new bank = 0.11 × The + 0.73 × river + 0.16 × bank**
> 73% of what “bank” now carries comes from “river”. Nobody wrote that rule; it was learned.

Three more facts about attention. First, no peeking. When learning to predict the next word, a token may only look at earlier tokens, otherwise it would just copy the answer. Like a cricket umpire who cannot use tomorrow's replay. This rule is called the causal mask.

Second, one attention pattern is not enough. So each layer runs several in parallel, called heads. One head might track who did what, while another links a word like it back to the noun it refers to.

Third, the cost. Every token scores every earlier token. So if you double the length of the prompt, the attention work roughly quadruples. That is another reason long prompts are slow and expensive.

**More about attention**

- No peeking: a token may only look at earlier tokens (the causal mask)
- Many heads: several attention patterns run side by side
- Cost grows with length squared: double the prompt, ~4x the work

*Another reason long prompts are slow and expensive.*

A short aside if you have done some machine learning. If not, just listen along. Attention is like weighted nearest neighbours, except the similarity measure itself is learned. The causal mask is the no look ahead rule from backtesting. And the final layer is multinomial logistic regression.

**Attention, in ML terms**

| You may know | In the transformer |
|---|---|
| Weighted k-nearest neighbours | Attention: a similarity-weighted average |
| No look-ahead in a backtest | The causal mask |
| Multinomial logistic regression | The final softmax layer |

## The rest of the layer

Attention is only half of each layer. Let's finish the picture.

After attention comes the feed forward network: a small neural network that works on each token separately. A useful split: attention moves information between tokens, and feed forward processes it within each token. Research suggests a lot of stored facts, like New Delhi being India's capital, live in these feed forward weights.

**Attention and feed-forward**

- **Attention**
  - Moves information between tokens
  - “bank” borrows from “river”
- **Feed-forward**
  - Processes each token on its own
  - A small network; much stored knowledge lives here

Models stack dozens of these layers. Two pieces of plumbing make that work. First, residual connections. Each layer does not replace a token's numbers. It adds a small correction to them. Like editing a draft, rather than rewriting the whole essay every time.

Second, normalisation. Before each layer, the numbers are rescaled to a standard size. Without it, after fifty layers, values could blow up to huge numbers or shrink to nothing. Normalisation keeps them in a sensible range.

**Residuals and normalisation**

- Residual: each layer ADDS a correction, it does not replace
- Like editing a draft, not rewriting it every time
- Normalisation: rescale numbers before each layer
- Keeps values from exploding or vanishing over many layers

After the last layer, the model takes the numbers at the final position and produces one score for every token in its vocabulary. Then a softmax, exactly like we did for river bank, turns them into probabilities. That is the prediction from part one of this day. Now you know where it comes from.

**Scores become probabilities**

> The top fund this week is  ____
- Bharat: 0.44
- Nifty: 0.27
- Deccan: 0.20
- a: 0.10

*One score per token in the vocabulary, then a softmax: just like the river bank.*

## Two families of transformer

One last thing: there are two main families of transformer, and you will meet both in real products.

Decoder only models use the causal mask, look only backwards, and are built for writing text. Every chat model, GPT, Claude, Gemini and Llama, is one. Encoder only models look in both directions, and are used to understand a whole text, for example to power search. Our chatbot will use both, by day five.

**Decoder-only vs encoder-only**

| Type | Looks at | Used for |
|---|---|---|
| Decoder-only | Earlier tokens only | Writing text: GPT, Claude, Gemini, Llama |
| Encoder-only | All tokens, both ways | Understanding text: BERT, search embeddings |

*Our chatbot: a decoder-only model talks; an embedding model searches.*

Quick check, with a calculator if you like. Pause and work it out: raw attention scores of one, zero and two. What weights does softmax give? The answer: about zero point two four, zero point zero nine, and zero point six seven.

**Quick check:** Raw attention scores are 1.0, 0.0 and 2.0. Roughly what weights does softmax give?

<details><summary>Answer</summary>

About 0.24, 0.09 and 0.67. Raise e to each score, add them up, divide each by the total.

</details>

Let's recap. Embeddings turn ids into learned numbers. Attention lets each token blend in the earlier tokens that matter. Feed forward processes each token, residuals add corrections, and normalisation keeps things steady. A final softmax gives the next token probabilities. Next video: how a raw model is trained into a helpful assistant.

- Embeddings turn token ids into learned lists of numbers
- Attention: each token blends in the earlier tokens that matter
- Feed-forward processes each token; residuals add, normalisation steadies
- A final softmax gives a probability for every next token
- Decoder-only models write; encoder-only models understand

The code for this series is linked in the description. Subscribe, and I will see you in the next video.

---

← [Day 1, Part 2](day01_p2.md) · [All lessons](README.md) · [Day 1, Part 4](day01_p4.md) →
