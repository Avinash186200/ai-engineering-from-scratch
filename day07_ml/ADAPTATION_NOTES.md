# Day 7 notes: adapting a model, and serving it

Companion to `lora_params.py` and the Day 7 episodes.

## 1. Prompt, retrieval or fine-tune?

Ask first: is the gap about **knowledge** (facts the model lacks) or **behaviour** (format, tone, a skill)?

| Need | First choice | Why |
|---|---|---|
| Facts that change, with citations | Retrieval (RAG) | Update the index, not the weights; you can show sources |
| Exact numbers from a system | A tool call | The model should never generate the number |
| A fixed output format | Prompt + structured output | Cheap, instant to change |
| A narrow skill at high volume | Fine-tune a smaller model | Lower cost and latency per call once it works |
| A house style the prompt cannot hold | Fine-tune (LoRA) | Behaviour lives well in weights |

Fine-tuning to add facts is the usual mistake: the facts go stale and the model cannot cite them.

## 2. Supervised fine-tuning in brief

- Data: a few hundred to a few thousand (instruction, ideal answer) pairs, cleaned and de-duplicated, with a held-out set.
- Loss masking: compute the loss only on the answer tokens, not on the prompt.
- Settings that matter: learning rate (small), epochs (1-3), and sequence length.
- Catastrophic forgetting: the model can lose general skills. Mix in some general data and re-run a general eval.

## 3. LoRA and QLoRA

- Freeze the weight matrix W (d x k) and learn a low-rank update dW = B A, with B (d x r) and A (r x k), r small (8-64).
- Trainable parameters per matrix drop from d*k to r*(d+k). For d = k = 4096 and r = 8: 16.8 M down to 65,536.
  `python day07_ml/lora_params.py` does this arithmetic for a whole model.
- A scaling factor alpha / r controls how strongly the update is applied.
- Usually applied to the attention projections; adding the MLP layers helps for harder tasks.
- QLoRA: keep the frozen base in 4-bit precision and train the LoRA matrices in higher precision. Fits large
  models on one GPU.
- Adapters are small files, so one base model can serve many tasks by swapping adapters.

## 4. Preference tuning

- RLHF: train a reward model on human rankings, then optimise the model against it with a penalty for drifting
  too far from the original.
- DPO: skip the reward model; train directly on (prompt, preferred, rejected) triples with a loss that raises the
  preferred answer's likelihood relative to the rejected one.

## 5. Distillation

A large "teacher" model labels many examples; a small "student" learns to copy its outputs. You get most of the
quality for a fraction of the serving cost on one narrow task. Check the provider's terms before training on outputs.

## 6. Serving open-weight models

- **Quantization**: store weights in 8 or 4 bits instead of 16. Memory roughly halves or quarters; quality drops
  a little, so evaluate after.
- **KV cache**: during generation the model keeps the keys and values of earlier tokens so it does not recompute
  them. It grows with context length and batch size, and is often what fills GPU memory.
- **Batching**: serving engines (vLLM and similar) batch requests continuously, which raises throughput a lot.

## 7. API model or open weights?

| Factor | Hosted API | Open weights, self-hosted |
|---|---|---|
| Quality on hard tasks | Usually higher | Catching up, varies |
| Data control | Depends on the contract | Full |
| Cost at low volume | Low | High (idle GPUs) |
| Cost at high, steady volume | Can get large | Can be lower |
| Operations work | Small | Large |

A common middle path is **routing**: a small, cheap model handles easy requests and a cascade escalates to a
larger model when the small one is unsure or fails a check.

## 8. Evaluating an adaptation

Run the same golden set before and after, on the task and on a general benchmark. Report both gains and losses,
and compare with the cheaper alternative (a better prompt, or retrieval) you tried first.
