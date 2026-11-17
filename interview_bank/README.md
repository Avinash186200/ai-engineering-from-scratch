# Interview question bank

Questions grouped by topic. Say each answer out loud in 30-60 seconds before you read the model answer.
The answers use this repo's running project (a research assistant over synthetic fund data) or a generic
forecasting or churn model as examples. Replace them with your own work when you practise.

## Practical questions (this folder)

| File | Topic | Questions |
|---|---|---|
| [`llm_fundamentals.md`](llm_fundamentals.md) | Tokens, sampling, hallucination, context, embeddings, prompting | 18 |
| [`rag_in_practice.md`](rag_in_practice.md) | Chunking, hybrid search, reranking, PDFs, freshness, debugging | 16 |
| [`agents_and_tools.md`](agents_and_tools.md) | Agent vs chatbot, tool design, MCP, memory, loops, failures | 16 |
| [`context_cost_memory.md`](context_cost_memory.md) | Context engineering, caching, routing, memory design | 8 |
| [`production.md`](production.md) | Deploy, outages, cost spikes, latency, versioning, scaling | 14 |
| [`evaluation.md`](evaluation.md) | Golden sets, judges, hallucination detection, metrics | 8 |
| [`design_choices_and_behaviour.md`](design_choices_and_behaviour.md) | "Why not X?", trade-offs, behavioural | 14 |

## Topic banks in the day folders

| Topic | File |
|---|---|
| Git, GitHub, CI/CD, Docker | [`day11_git_docker/INTERVIEW_QA.md`](../day11_git_docker/INTERVIEW_QA.md) |
| LLMOps and observability | [`day12_llmops/INTERVIEW_QA.md`](../day12_llmops/INTERVIEW_QA.md) |
| Cloud deployment | [`day13_cloud/INTERVIEW_QA.md`](../day13_cloud/INTERVIEW_QA.md) |
| Data pipelines | [`day14_pipelines/INTERVIEW_QA.md`](../day14_pipelines/INTERVIEW_QA.md) |
| Testing | [`day15_testing/INTERVIEW_QA.md`](../day15_testing/INTERVIEW_QA.md) |
| Security | [`day16_security/INTERVIEW_QA.md`](../day16_security/INTERVIEW_QA.md) |
| Models as a product | [`day17_product/INTERVIEW_QA.md`](../day17_product/INTERVIEW_QA.md) |
| AI agents in production (video) | [`interview_special/README.md`](../interview_special/README.md) |
| How architectures evolve | [`arch_evolution/`](../arch_evolution/) |
| Lessons learned | [`lessons_learned/INTERVIEW_QA.md`](../lessons_learned/INTERVIEW_QA.md) |
| System design and STAR | [`system_design/`](../system_design/README.md) |

## How to practise

1. Pick a file, cover the answers, and answer aloud with a timer.
2. Mark the ones you could not answer in under a minute. Repeat only those the next day.
3. For every answer, add one sentence about something you built or ran yourself. That sentence is what makes
   an answer believable.

## Practise with flashcards

[`make_flashcards.py`](make_flashcards.py) turns every question in the banks listed above into a card in
[`flashcards.csv`](flashcards.csv) (310; for `system_design/`, only the follow-up probes). Each answer is its
first whole sentences, up to 80 words, then the file with the rest. The third column is the topic, used as a tag.

After you change any question file, rebuild it. CI fails if the file is out of date
(`day15_testing/test_flashcards.py`).

```bash
python interview_bank/make_flashcards.py
```

- **Anki**: File > Import and pick `flashcards.csv`. Set the field separator to Comma and turn Allow HTML off. Map
  column 1 to Front, column 2 to Back and column 3 to Tags. The header row comes in as one extra card: search
  `tag:tags` and delete it.
- **Quizlet**: open the file in a spreadsheet, copy the question and answer cells without the header row, and
  paste them into Quizlet's import box. Choose Tab between term and definition and New line between cards.
