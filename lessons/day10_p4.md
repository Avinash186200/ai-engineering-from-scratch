# Day 10, Part 4: Behavioural Interview Tips for AI Engineers (STAR Method) + Series Finale

**Watch:** [youtu.be/QSGntDMA9N0](https://youtu.be/QSGntDMA9N0) · **Code:** [`day10_mock/`](../day10_mock/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

The final episode of the series: the behavioural round, how to score your mock honestly, and what to do before and after every real interview.

## What you will learn

- The STAR method, and how to keep every story under two minutes
- The five stories every AI engineer should prepare
- Model answers: "tell me about yourself", a mistake, a disagreement, your weakness, first 90 days
- The three questions to ask your interviewer
- Scoring your mock honestly and the go / no-go decision
- Where to go after this series

## Chapters

- [0:00](https://youtu.be/QSGntDMA9N0?t=0) Intro
- [0:40](https://youtu.be/QSGntDMA9N0?t=40) The STAR method
- [1:31](https://youtu.be/QSGntDMA9N0?t=91) Five stories to prepare
- [2:09](https://youtu.be/QSGntDMA9N0?t=129) Story: a system you built
- [2:43](https://youtu.be/QSGntDMA9N0?t=163) Story: a mistake
- [3:39](https://youtu.be/QSGntDMA9N0?t=219) The questions everyone gets
- [3:48](https://youtu.be/QSGntDMA9N0?t=228) The questions everyone gets
- [5:36](https://youtu.be/QSGntDMA9N0?t=336) Score yourself honestly
- [7:27](https://youtu.be/QSGntDMA9N0?t=447) You made it to the end

## Lesson notes

Slide content and the full narration, in order.

Welcome back to the final episode of the series. In the last part we wrote an agent and a retriever from a blank file. Now the last round: behavioural, where they test how you think and work with people.

Many engineers treat this round as a chat, and that is a mistake. It tests judgement, ownership and how you work with people. For senior roles, close decisions are often made right here. And the difference between a rambling story and a sharp one is simply preparation.

**Behavioural rounds decide close calls**

- They test judgement, ownership, and teamwork
- Senior roles are often won or lost here
- Unprepared stories ramble; prepared ones land in two minutes

## The STAR method

The standard format for every story is called STAR.

Situation: one sentence of context. Task: what you owned. Action: what you decided and did, including the trade offs. And Result: an outcome, ideally with a number, plus the lesson you took away. Most of the two minutes goes on the action. Keep the situation short; nobody hires you for the background.

**STAR: four parts, under two minutes**

1. Situation: one sentence of context
2. Task: what you personally owned
3. Action: what you decided and did, with the trade-offs
4. Result: an outcome with a number, plus the lesson

*Most of the time goes on Action. Keep Situation short.*

One small rule that interviewers listen for closely. Say we for team work, I for what you personally did, and I led for what you owned. Claiming the whole team's work as your own is spotted quickly, and it costs you trust.

**We, I, and I led**

> **“We” for team work. “I” for what you did. “I led” for what you owned.**
> Interviewers listen closely for this. Never claim the team's work as yours alone.

## Five stories to prepare

You do not need fifty stories. Five well prepared ones can answer almost any behavioural question.

One: a system you built end to end. Two: a time you told someone a hard truth, like results that were not as good as hoped. Three: a mistake in production. Four: disagreeing with a reviewer or a senior colleague. Five: helping a team or a person grow. Write them down, with real details from your own notes.

**Five stories cover most questions**

| Story | Use it for |
|---|---|
| A system you built end to end | “Walk me through your work” |
| Telling someone a hard truth | Integrity, communication |
| A mistake in production | Ownership, incidents |
| Disagreeing with a reviewer | Conflict, review culture |
| Helping a team grow | Leadership, mentoring |

Here is a story built from our own series project. Situation: analysts wanted to ask about funds in plain English. Task: I owned the design and the build. Action: an agent that calls the fund ranking tool, with a rule that numbers only come from the tool, and a golden set run on every change. Result: answers matched the model's numbers exactly, and the tests caught regressions before users did.

**“Walk me through a system you built”**

1. S: analysts wanted to ask fund questions in plain English
2. T: I owned the design and build of the assistant
3. A: agent + ranking tool; numbers only from the tool; a golden set
4. R: answers matched the model exactly; tests caught regressions

The mistake story scares people, but it is a gift. Pick a real one, and show calm ownership. For example: a bulk data load changed a field in a way another program did not expect, and data went missing. We rolled back first, found the root cause, then fixed it properly. And the lesson: I now check every downstream reader before a bulk change.

**“Tell me about a mistake in production”**

1. S: a bulk data load on a test server
2. T: I owned the load
3. A: a field changed in a way a downstream reader didn't expect
4. R: roll back first, then root cause, then a proper fix
5. Lesson: I now trace every downstream reader before a bulk change

For a disagreement, show a process, not a fight. Before replying, work out why the rule exists. Test the claim directly. Check whether the same problem exists in sibling code. Then reply with evidence, not opinion. The interviewer wants to see that you can be convinced, and that you can convince.

**“Tell me about a disagreement”**

- Before replying, work out why the rule exists
- Test the reviewer's claim directly
- Check if the same issue exists elsewhere in the code
- Reply with evidence, not opinion
- Show you can be convinced, and can convince

## The questions everyone gets

Now the questions that come up in almost every behavioural round. Prepare these word for word.

Tell me about yourself. Three moves in two minutes. Where you are now, and the scale you work at. One signature piece of work, with one result. And what you want next, and why this role fits it. Not your whole life story. Rehearse it out loud until it feels natural.

**A two-minute pitch in three moves**

**Now** (your role and the scale you work at) → **Signature work** (one system, with one result) → **Next** (what you want, and why this role)

*Rehearse it out loud until it feels natural.*

Your biggest weakness: give a real one, plus what you are doing about it. For example, my LLM experience is newer than my other skills, so I built every piece myself, from agents to evaluation. And why are you leaving? Thirty seconds, neutral, and forward looking. Never complain about people or money.

**Weakness, and why you're leaving**

- **Biggest weakness**
  - A real one, not a disguised strength
  - Plus what you're doing about it
  - e.g. “my LLM experience is newer; I've built every piece in a course like this”
- **Why leaving?**
  - Thirty seconds
  - Neutral and forward-looking
  - No complaints about people or money

What would you do in your first ninety days? First month: listen and learn. Run the system, sit with users, and find out how quality is measured today. Second month: ship something small and useful, and if there is no evaluation set, help build one. Third month: own a meaningful piece, with a clear measure of success.

**Listen, ship small, then own**

1. Days 1–30: learn the system, sit with users, find how quality is measured
2. Days 31–60: ship something small; help build an eval set if none exists
3. Days 61–90: own a meaningful piece, with measurable success

And at the end, they will ask: any questions for us? Never say no. Ask three. How do you evaluate LLM features before they ship? What is the path from a merged change to production? And what would make someone clearly successful in six months? Add one question specific to their product.

**Always ask three**

- “How do you evaluate LLM features before they ship?”
- “What does the path from a merged change to production look like?”
- “What would make someone in this role clearly successful in six months?”

*Plus one question specific to their product.*

## Score yourself honestly

You have done all four rounds. Now score them, and be honest, because a flattering score helps nobody.

Score each round from one to five on these areas. Concept accuracy. A real example. Structure and timing. Handling probes. And for the coding round, whether it runs. Score from the recording, write one sentence of evidence for each score, and if your AI interviewer scored you too, keep the lower of the two.

**Score each round from 1 to 5**

| Area | 1 | 5 |
|---|---|---|
| Concept accuracy | Vague or wrong | Precise, with trade-offs |
| Real example | None | Specific, honest, quantified |
| Structure and timing | Rambling | Clear, within time |
| Handling probes | Bluffs | Reasons it out, admits gaps |
| Coding | Doesn't run | Runs, and explained |

A few hard rules. Any bluff caps your probes score at one. Going over two and a half minutes caps structure at three. Code that did not run in time scores one or two, however close it was. Score only the first attempt. And you are ready when you average four or more on concepts and probes.

**Rules that keep the score honest**

- Any bluff: probes score capped at 1
- Over 2:30 on a technical answer: structure at most 3
- Code didn't run in 20 minutes: coding is 1 or 2
- Score the first attempt only
- Ready when you average 4+ on concepts and probes

And after every real interview, within one hour, write down every question you were asked. Write a better answer for the weak ones. Check that every claim you made was accurate. And score it on the same rubric. Over a few interviews, the trend tells you exactly what to drill next.

**Within one hour**

1. Write down every question you were asked
2. Write a model answer for each weak one
3. Check every claim you made was accurate
4. Score it on the same rubric, and track the trend

Quick check, the last one of the series. In a STAR story, which part should take most of your two minutes? Pause and answer. The action: what you decided and did, and the trade offs. That is where the interviewer actually sees your judgement.

**Quick check:** In a STAR story, which part should take most of your two minutes, and why?

<details><summary>Answer</summary>

Action: what you decided and did, with the trade-offs. That is where the interviewer sees your judgement.

</details>

## You made it to the end

And that brings us to the end of the series. Let's look back at how far you have come.

Ten days ago, a large language model was a mystery. Now you know it is a next token classifier. You have written structured prompts, built an agent with tools, served those tools over MCP, built retrieval, tested it with a golden set, validated a model properly, put it in production, designed systems, and practised the interview.

Where to go from here? Rebuild the research assistant chatbot yourself, from a blank repository. Extend it with your own tools and documents. Keep a weekly ninety minute drill. And write about what you built, because that becomes your strongest interview story.

**Keep building, keep practising**

- Rebuild the research assistant chatbot yourself, from a blank repo
- Extend it: new tools, new documents, new golden cases
- Drill 90 minutes a week: three questions, one design, one coding task
- Write about what you built; it becomes your interview story

If you remember one thing from all ten days, remember this. The model computes, the LLM explains, and you check. Grounded answers, honest testing, and no bluffing. It is how good AI products are built, and it is how good interviews go too.

**The rule that runs through it all**

> **The model computes. The LLM explains. And you check.**
> Grounded answers, honest tests, and no bluffing: in products and in interviews.

A final recap. STAR with a short situation and a long action. Five stories cover most questions. Prepare your pitch, your weakness, your ninety days and your three questions. Score honestly. And keep building. Next stop: your first real interview.

- STAR: short Situation, long Action, a Result with a lesson
- Five stories answer most behavioural questions
- Prepare the pitch, the weakness, 90 days, three questions
- Score from the recording; any bluff caps you at 1
- Keep building and drilling every week

Thank you so much for learning with me across these ten days. All the code is linked in the description. Tell me in the comments when you land that AI engineering role. Best of luck, and keep building.

---

← [Day 10, Part 3](day10_p3.md) · [All lessons](README.md)
