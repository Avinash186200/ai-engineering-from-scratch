# 6. Fine-tuning reality: format, not facts

**Public repo:** [llm-finetuning-lora](https://github.com/Avinash186200/llm-finetuning-lora).

## The problem

Teams fine-tune to "teach the model our data". LoRA is cheap, so it is tempting. What does it actually change?

## What went wrong

- **The silent truncation bug.** My first run used `max_len: 192`. The prompt was about 161 tokens and the answer
  about 50, so every example was cut before the closing brace and the end token. Val loss looked great
  (**0.006**), because the loss only covers tokens that are present. The model never learned to stop. It wrote the
  right fields, then kept inventing keys until the cap. Test JSON validity was **22%**.
- **Expecting facts.** I asked each tuned model for 30 values it saw in training. It got **0 of 30**, the same as
  the base model.
- **Expecting understanding.** On a hard set, LoRA stayed valid (98.8 to 100%) but exact match fell to 26 to 30%.
  It learned my templates, not the task.

## The fix

- Raised `max_len` to 320. The same run scored **100%** valid JSON.
- `encode_example` now **raises** if any example would be truncated, and a test checks it. One assertion.
- Use fine-tuning for format and behaviour: zero-shot gave no valid JSON, few-shot 46 to 52%, LoRA 100% on test.
- Put facts in the context (RAG), not in the weights.

## How to spot it next time

- Loss is very low and the outputs are bad: read the outputs.
- Check the token length of prompt + answer against `max_len` before training.
- Probe for facts the model saw in training. If it cannot recall them, fine-tuning is not your knowledge store.

## Say it in an interview

> My LoRA run had a val loss of 0.006, and only 22% of outputs were valid JSON.
> The max length cut every example before the closing brace, so the model never learned to stop.
> I raised the length and added an assertion that fails if any example would be truncated.
> Validity went to 100%.
> But it learned format, not facts: it recalled 0 of 30 training values, so facts go in RAG.
