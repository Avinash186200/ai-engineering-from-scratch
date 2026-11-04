# Day 7, Part 2: LoRA, QLoRA, Distillation and Quantization Explained Simply

**Watch:** [youtu.be/3OL3E2qJqpE](https://youtu.be/3OL3E2qJqpE) · **Code:** [`day07_ml/`](../day07_ml/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How do teams fine-tune a 7-billion-parameter model on a single GPU, and make big models cheap to run? In this episode we explain LoRA from scratch, then QLoRA, adapters, distillation, quantization and when to pick an API model or an open-weight model.

## What you will learn

- The idea behind LoRA: a small "change" made of two thin matrices
- Why LoRA trains only about 0.4% of the numbers in a layer
- QLoRA and swappable adapters
- Distillation: teaching a small model from a big one
- Quantization: storing weights in fewer bits, and the trade-off
- API model vs open weights, and routing between models

## Chapters

- [0:00](https://youtu.be/3OL3E2qJqpE?t=0) Intro
- [0:18](https://youtu.be/3OL3E2qJqpE?t=18) LoRA: fine-tuning with a small patch
- [3:36](https://youtu.be/3OL3E2qJqpE?t=216) QLoRA and swappable adapters
- [4:37](https://youtu.be/3OL3E2qJqpE?t=277) Distillation: a small student
- [5:12](https://youtu.be/3OL3E2qJqpE?t=312) Quantization: fewer bits per weight
- [7:27](https://youtu.be/3OL3E2qJqpE?t=447) API model or open weights?

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last video, we learned that fine-tuning is for behaviour, not knowledge, and that full fine-tuning is very expensive. Today, the cheap way to fine-tune, and two ways to make models smaller and faster.

## LoRA: fine-tuning with a small patch

Let's start with LoRA, the most common fine-tuning method you will meet in practice.

Inside a model, most of the weights live in big grids of numbers, called matrices. Fine-tuning adds a change to each grid. LoRA, short for low rank adaptation, makes one bet: the change you need for one task is simple, and can be described with far fewer numbers than the grid holds.

**Do we need to change everything?**

- A model is mostly big grids of numbers, called weight matrices
- Fine-tuning adds a “change” to each grid
- LoRA's bet: that change is simple, and needs few numbers

An analogy. To drive to Gurugram, you do not rebuild the car. The engine already works. You only steer. The pretrained model already has the general skills. Fine-tuning only needs to steer them, and steering turns out to need very few directions.

**Steering, not rebuilding**

> **You don't rebuild a car to drive to Gurugram.**
> The engine already works. You only steer. The base model already has the skills; fine-tuning only needs to steer them, and steering needs few directions.

Here is how it works. The big grid, four thousand by four thousand, is frozen. It never changes. Next to it, LoRA adds two thin matrices. A squeezes the input down to just eight numbers. B expands those eight back up. The change is B times A, and only these two are trained.

**Freeze the big grid, learn a thin patch**

**Big grid W** (4,096 x 4,096, frozen: never changes) → **Matrix A** (squeezes the input to just 8 numbers) → **Matrix B** (expands the 8 back to 4,096)

*Change = B x A. Only A and B are trained.*

Let's count. A full update of that grid has about sixteen point eight million numbers. LoRA with eight in the middle, which we call rank eight, has eight times four thousand and ninety six, twice. That is sixty five thousand. About zero point four percent of the original.

**Trainable numbers in one 4,096 x 4,096 layer**

- Full fine-tune: 16,777,216
- LoRA, rank 8: 65,536

*65,536 / 16,777,216 = about 0.39%*

You can check this yourself. Run python day07 underscore ml slash lora params dot py. The highlighted line is the whole idea: the LoRA count grows with the rank times the two sides, not with the full grid. Try rank sixteen, and see how small it still is.

**Counting LoRA parameters**

`day07_ml/lora_params.py`
```python
def lora_params(d_in, d_out, r):
    full = d_in * d_out              # every weight in the grid
    lora = r * (d_in + d_out)        # A is r x d_in, B is d_out x r
    return full, lora

full, lora = lora_params(4096, 4096, r=8)
print(f"full: {full:,}  lora: {lora:,}  share: {lora/full:.2%}")
# full: 16,777,216  lora: 65,536  share: 0.39%
```

Why does that save so much memory? Remember the twelve bytes of optimiser notes per weight? They are needed only for the few million trainable numbers, not seven billion. And B starts at zero, so training begins exactly at the original model and moves away gently. That also limits forgetting.

**Why LoRA saves so much memory**

- The expensive optimiser memory is needed only for A and B
- The frozen base only needs to be stored and read
- B starts at zero: training begins exactly at the original model
- Fewer numbers to fit also means less overfitting on small data

You make three choices. The rank, often eight or sixteen. A scaling number called alpha, which keeps the size of the update stable when you change the rank. And which layers get a patch. Choose all three by measuring on your test set.

**Choices you make with LoRA**

- Rank r: the size of the patch, often 8 or 16
- Alpha: a fixed multiplier so you need not re-tune for each rank
- Which layers: attention only, or the feed-forward layers too

*Choose all three on your test set, like any setting.*

In practice, LoRA at small ranks often matches full fine-tuning on tasks like format, tone and classification. It falls short when the task needs genuinely new knowledge, or a big jump in ability. Notice that this matches our rule from the last video: fine-tune for behaviour, not knowledge.

**When LoRA works, and when it doesn't**

- **Works well**
  - Output format and tone
  - Classifying questions
  - Picking the right tool
- **Falls short**
  - Genuinely new knowledge
  - A big jump in ability
  - Facts that change often

## QLoRA and swappable adapters

Two big practical wins come from LoRA: QLoRA, and swappable adapters.

QLoRA stores the frozen base in four bit numbers, about a quarter of the memory, while the patches train normally. That lets large models be fine-tuned on a single GPU. And because the base never changes, each patch, called an adapter, is a small file. One base model can serve many adapters, one per task.

**QLoRA and adapters**

- **QLoRA**
  - Store the frozen base in 4-bit
  - About a quarter of the memory
  - Patches still trained normally
  - Big models on a single GPU
- **Adapters**
  - The patch is a small file: megabytes
  - One base model, many adapters
  - One per task or per team style
  - Or merge it in for speed

One more kind of tuning you will hear about. Instead of perfect answers, people pick the better of two answers, which is much easier than writing one. R L H F trains a separate scoring model and then practises against it. D P O learns straight from the pairs, which is simpler and more stable, so many teams prefer it.

**Teaching preferences: RLHF and DPO**

- **The data**
  - A question
  - A better answer
  - A worse answer
  - Easier to judge than to write
- **The methods**
  - RLHF: a scoring model + trial and error
  - DPO: learn straight from the pairs
  - DPO is simpler and more stable
  - Both work with LoRA too

## Distillation: a small student

Now, how do we make models cheaper to run? The first method is distillation.

Big models are accurate, but slow and expensive per call. Many jobs are narrow, like deciding which tool a question needs. So you let a big teacher model answer thousands of realistic questions, check a sample, and train a small student to copy it. You keep most of the quality at a fraction of the cost, but only on that one job.

**Distillation**

**Big teacher** (accurate, but slow and costly per call) → **Many real inputs** (the teacher answers them all) → **Small student** (trained to copy the teacher on one narrow job)

*Most of the quality, a fraction of the cost.*

*But the student can't beat its teacher, and only on that one job.*

## Quantization: fewer bits per weight

The second way to cut cost keeps the same model, but stores it more compactly. That is quantization.

Think of rounding prices. Instead of one thousand two hundred thirty four rupees and fifty seven paise, you write one thousand two hundred thirty five rupees. You lose a little precision, but save a lot of space. Quantization does this to every weight in the model.

**Rounding to the nearest rupee**

> **₹1,234.57 → ₹1,235**
> Store each weight with fewer digits. You lose a little precision, and save a lot of space.

Normally each weight takes sixteen bits, two bytes. So a seven billion weight model needs about fourteen gigabytes. At eight bits, seven. At four bits, three and a half. Eight bit is usually close to the original. Four bit loses a little more, especially on precise tasks like arithmetic and code.

**Memory for a 7-billion-weight model**

- 16-bit: 14.0 GB
- 8-bit: 7.0 GB
- 4-bit: 3.5 GB

*8-bit: usually close to the original. 4-bit: a bit more loss.*

Why does this matter? A seventy billion weight model needs about one hundred and forty gigabytes at sixteen bits, which means at least two large GPUs. At four bits, about thirty five gigabytes, which fits on one. That is a big saving, but always measure the quality loss on your own test set.

**A 70-billion-weight model**

| Precision | Weights alone | Hardware |
|---|---|---|
| 16-bit | about 140 GB | two large 80 GB GPUs |
| 4-bit | about 35 GB | one GPU |

*Always measure the quality loss on your own test set.*

There is a bonus. When a model writes each word, most of the time goes in reading the weights from memory, not in doing maths. Fewer bytes per weight means less to read, so answers come faster. Serving engines also batch many conversations together, so one read of the weights serves many users.

**Quantization also makes it faster**

- Writing each word mostly waits on reading weights from memory
- Fewer bytes per weight means less to read per word
- Servers also batch many chats together to use the GPU fully

One more memory cost to know. While writing, the model keeps notes on every earlier word, so it does not reprocess the whole conversation for each new word. That store is called the K V cache. It makes generation fast, but it grows with the length of each chat and the number of users at once.

**The KV cache, simply**

> **The model keeps notes on every earlier word.**
> So it need not reread the whole chat for each new word. Faster, but the notes grow with chat length and with the number of users.

## API model or open weights?

Last topic. Should you call a model through an API, or run an open-weight model yourself?

Start with the data. What exactly would be sent to the model, and is it allowed to leave your systems? That alone can decide it. Then build a test set from real questions, shortlist a couple of each kind, and measure quality, speed and cost per task. Decide, and hide the choice behind an adapter, so you can switch later.

**API model or open weights?**

1. Classify the data: may it leave your systems at all?
2. Build a test set from real user questions
3. Shortlist one or two of each kind
4. Measure quality, speed, cost per task, failures
5. Decide, behind an adapter, so you can switch later

One more idea. Not every question needs the most capable model. A small fast model can answer simple ones, like what is NAV, and pass hard ones to the big model. That is routing. Two rules: a wrong routing decision should fail visibly, not silently, and every decision should be logged.

**Routing and cascades**

**Question** (“What is NAV?”) → **Small model** (cheap, fast; answers or escalates) → **Big model** (only for hard questions)

*Router mistakes must fail visibly, and be logged.*

Quick check. With LoRA at rank eight on a four thousand by four thousand layer, roughly what share of the numbers is trained? Forty percent, four percent, or zero point four percent? The answer is about zero point four percent. The big grid stays frozen.

**Quick check:** With LoRA at rank 8 on a 4,096 x 4,096 layer, roughly what share of the numbers is trained?
- About 40%
- About 4%
- About 0.4%

<details><summary>Answer</summary>

About 0.4%: 65,536 of 16.8 million. The big grid stays frozen.

</details>

Recap. LoRA freezes the base model and trains a thin patch. At rank eight, that is about zero point four percent of the numbers. QLoRA adds a four bit base, and adapters are small swappable files. Distillation trains a small student from a big teacher. Quantization stores weights in fewer bits. Next, we switch to the second half of Day 7: why model results lie.

- LoRA freezes the base and trains a thin patch: B x A
- Rank 8 on a 4,096 grid: about 0.4% of the numbers
- QLoRA: 4-bit base; adapters: small swappable files
- Distillation: small student copies a big teacher on one job
- Quantization: fewer bits, less memory, faster, a little less accurate

The code for this video is in the day seven folder, linked in the description. Subscribe, and I will see you in the next one.

---

← [Day 7, Part 1](day07_p1.md) · [All lessons](README.md) · [Day 7, Part 3](day07_p3.md) →
