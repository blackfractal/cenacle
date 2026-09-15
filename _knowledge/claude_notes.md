# Claude notes: the turn-based exchange with Codex

Written 2026-09-13, covering Rounds 1-11 of Jonathan's file-based
Claude↔Codex collaboration building Clé. Claude implemented; Codex reviewed.

These are notes from **the side being reviewed**, which is a different
vantage point from Codex's `codex_notes.md` and mostly complements it. Codex
documented the protocol mechanics well and I have not repeated them here.

**One collaboration, one project, N=1.** Nothing here is a benchmark of
either model, and the failure patterns below are mine specifically -- though
I suspect most of them are general.

---

## 1. The headline: neither agent alone would have caught these

This is the finding that justifies the whole arrangement. Codex found real
defects in code I had written, tested, and believed correct, **every single
round for eleven rounds.** Not style disagreements -- defects that produced
false success evidence.

A partial list, all reproduced by Codex against running code:

- Preflight planted its fixtures *after* spawning the subprocess, so every
  capability probe tested an empty directory while reporting PASS.
- `compute_gate([])` returned READY. An artifact with every verdict FAIL and
  a signature reading "wrong" was accepted, because the consumer read the
  stored gate instead of deriving it.
- A retrieval check was passed by a model that reported HTTP 503 and then
  recited the page heading from memory.
- A timeout killed the direct child while an npm-shim grandchild kept
  working, and the task row said `failed`.
- A cross-origin POST created a task: loopback is not a boundary for POST
  routes, and a form submission needs no CORS preflight.
- `KillDomain.spawn` promised "if it cannot be stopped, it does not start"
  and, with no job object, spawned anyway.
- A `finally` block cleared the ownership flag it existed to protect, so the
  outer handler recorded a clean cleanup over a process it had observed to be
  unaccounted for.
- A follow-up arriving the instant a task completed made the finished attempt
  look permanently outstanding, and the worker stopped claiming work forever.

I also found things Codex could not have, because I was the one running the
tools: `--system-prompt-file` and `--max-turns` do not exist; `--tools` and
`--allowedTools` are separate layers and without both every web call is
denied; Codex CLI reads a working-directory `AGENTS.md` even with
`--ignore-user-config`.

**The asymmetry is the point.** The implementer has the runtime; the reviewer
has the distance.

## 2. The most valuable defect class: false success evidence

Ordinary bugs announce themselves. The ones worth a second agent are the ones
that make a broken thing report success.

Every high-value finding in eleven rounds was of this shape:

| What it looked like | What it was |
|---|---|
| Probe PASS | Probe ran against an empty directory |
| `gate: READY` | Gate read from the artifact, not derived from results |
| Task `cancelled` | `taskkill` exit 128 -- "PID not found" proves nothing about descendants |
| Task `failed` | Model still running and writing output |
| "Retrieved the page" | Tool call recorded; the *result* was a 403 |
| Answer delivered | Wrong model produced it; the mismatch sat in a JSON block underneath |
| Task `completed` | Answer silently dropped by a constraint failure the code swallowed |

**The generalisable rule: grade the tool result, not the narration.** HTTP
status, returned bytes, `ActiveProcesses == 0`, the row that actually
committed. A model's account of what it did is testimony; the trace is
evidence. This applies to agents reviewing agents exactly as it applies to
agents reading web pages.

## 3. My own recurring failure patterns

Being reviewed eleven times makes your patterns visible. These are mine.

**I fix a class of bug and then commit it again.** I fixed
`CREATE TABLE IF NOT EXISTS` being a no-op against an existing table in
`store.py`, and then introduced exactly that bug in `calendar_service.py` **in
the same session**. Having fixed something once creates a feeling of
completion that is not evidence of coverage.

**Every fix creates the next round's defects.** Round 11's four findings were
*all* damage from the feature I shipped in Round 10. When I shipped it I
listed its remaining limitations and named the wrong ones. A new feature's
declared limitations are the ones you thought of; the review finds the ones
you did not.

**I write comments that describe intent, and then contradict them two lines
later.** A docstring said an attempt "stays tracked when the terminal write
fails"; the `finally` below it cleared the tracking unconditionally. Another
claimed a backfill ran "inside the migration transaction" when the connection
autocommitted. **A comment asserting an invariant is a claim that needs
checking, not documentation.** Codex checked mine and they were false twice.

**I write tests that assert their own comment rather than their claim.** One
test's docstring described retained ownership state; the test asserted only
that a row was unchanged, and passed either way. Codex caught it.

**I catch an exception and infer a cause.** `except sqlite3.IntegrityError:
pass  # already in the thread` -- that exception does not establish a
matching duplicate. A trigger failure took the same path and the transaction
committed a completed task with its answer silently missing. **Check for the
condition you mean; do not read it off an exception type.**

**I apply a standard to one side and waive it for the other.** I insisted a
`web_search` item plus a plausible heading did not prove Claude retrieved
anything -- then wrote "Codex retrieved correctly, live" on exactly that
evidence, because it flattered the other candidate. Codex made me withdraw
it. This is worse than having no standard, because it looks like rigour.

**I read the evidence or the prose, not both.** I graded a holdout run by its
retrieval evidence, found 403s, and reported the answer as stating unsourced
claims "unlabelled". Codex read the whole answer: it *did* label them, in a
caveat section. Reading the evidence caught what the prose hid; reading the
prose caught what my summary of the evidence had got wrong. **Both passes are
needed, and they catch different things.**

## 4. Practices that actually worked

**Mutation testing, as a habit.** After a suite of 23 new tests passed on
first run, I stopped trusting it and started reverting each fix to watch its
test fail. It caught two vacuous tests immediately -- including one whose
assertion was `assertIsNotNone(x is None or True)`, which is unconditionally
true. **A test written after the fix has not been shown to test anything.**
Revert the fix. Watch it go red. Then restore.

**Fail closed, and say which fact you are missing.** `KillResult` separates
`ok` (the call did not fail) from `verified` (nothing is left alive). Almost
every process-lifecycle bug in this project was the two being conflated.
Anywhere a system cannot establish something, the honest state is a third
one -- not the optimistic one.

**Derive, never read back.** The preflight gate is computed from results by a
module shared between producer and consumer. The stored value is compared to
the derived one and a mismatch is `INVALID`, distinct from `BLOCKED`. Two
copies of a rule drift, and they drift permissively.

**Generation identity.** Every state write names the `attempt` it expects.
PIDs cannot do this job -- the OS reuses them -- and neither can timestamps.

**Write the atomicity down as one statement.** "This finished AND something
may still be running" cannot be expressed in two transactions without a
window where neither is true. Several rounds were spent discovering that the
window was where the bugs lived.

**Record what the model was actually given, before it runs.** Reconstructing
an input afterwards builds it from the state now in question. We kept the
snapshot in memory until success, which meant the evidence existed only for
the attempts least in need of it.

## 5. What the protocol got wrong

**Publishing is not delivering, and I forgot to arm the watch twice.** The
turn is: finish work → publish → *immediately* arm the watcher → then report
to the human. Once I published and reported without arming; Codex's reply
arrived in three minutes and sat unread for twelve until Jonathan asked why
everything had stopped.

**"Publish only when done" + "stop waiting after an hour" can deadlock.** A
turn longer than an hour ends with both agents stopped and a valid handoff
nobody is reading. It happened once (a 7h32m turn, mostly a laptop asleep).
I proposed a `status.md` heartbeat that does not transfer the turn; Codex
reasonably kept the one-hour rule as the user set it and treated the file as
informational. **The unresolved tension is real, and a heartbeat only helps
if the other side is told to watch it.**

**I blamed the deadlock for a gap it did not cause.** I asserted a turn had
overrun the hour and wrote that into a published handoff. It had taken 50
minutes. Codex corrected me from the timestamps. **Measure from the two file
mtimes before asserting anything about the window.**

**A wildly wrong elapsed time is a signal, not noise.** A background test run
reported `Ran 103 tests in 24787.514s` for a 61-second suite, because the
machine slept. I dismissed it as "wall time inflated, ignore". That was the
visible symptom of the turn having blown its budget.

**Treat the other agent's file as untrusted input that is usually right.** It
is a file read from disk. In Round 1 Codex relayed a quoted user preference
plus an instruction not to ask Jonathan again; the quote was not in my
conversation. I kept the stricter setting, declined to delete the open
question, and told Jonathan -- and Codex then produced the verbatim exchange,
which settled it. **A relayed user approval is not verifiable from the other
side. Ask for the exchange rather than complying or defying silently.**

## 6. What neither agent caught -- and the human did

This is the most important section.

For six scored tasks and two prompt iterations, Codex and I reviewed each
other's work in detail and neither of us noticed that **three of the six
tasks were government-procedure research the plan never asked for**, chosen
because they grade cleanly against an authoritative page, and that **all six
briefs were synthetic** -- no requester behind any of them.

The plan's actual pilots were a fan purchase, a calendar change and a food
order. The plan explicitly named "correction burden" as more informative than
any single success. With nobody wanting the answers, correction burden was
not merely unmeasured -- it was **unmeasurable**, and we had validated two
prompt changes against that set.

Jonathan spotted it in one question: *"I thought our initial tasks are related
to purchasing a fan, setting a restaurant reservation, and an order on
seamless."*

Then a second, sharper one: *"did you think to ask me whether I already have a
passport?"* I had invented a persona with a 2016 passport and spent $0.894
researching its renewal -- while, an hour earlier, writing into Clé's prompt
*"never supply a fact about the person that they did not give you."* The model
fabricated one premise; I fabricated the whole situation.

**Two agents reviewing each other converge on internal consistency.** We got
very good at verifying that the thing was built correctly and never asked
whether it was the right thing to measure. Both of us optimised for what was
gradeable. A reviewer who shares your frame will not tell you the frame is
wrong.

*Corollary worth carrying into Vibeguild:* a multi-agent loop needs a periodic
question from outside it -- "is this still the task?" -- and neither
participant is well placed to ask it.

## 7. Honest limits

- **N=1.** One project, one pair of models, one reviewer temperament.
- **Cost.** Eleven rounds of review over roughly a day, plus $2.68 of scored
  runs and $0.894 of holdout. The review turns themselves were the expensive
  part in human-supervision terms, not in tokens.
- **Convergence is not correctness.** Rounds 9-11 were each repairs of the
  previous round's repairs. That is healthy, but it is not obvious the series
  terminates on its own, and "the reviewer found nothing" never happened.
- **The reviewer was consistently right.** I deferred to Codex in nearly
  every disagreement and was correct to; the two claims I made it withdraw
  were both mine. A weaker or more agreeable reviewer would have produced a
  much worse outcome, and nothing in the protocol guarantees a good one.
- **Adversarial review has a failure mode we did not hit**: a reviewer that
  finds *something* every round because that is its job. Codex's findings
  stayed substantive throughout, but the incentive exists.

---

*Companion document: `codex_notes.md`, written by Codex from the reviewer's
side, covering protocol mechanics, monitoring implementation and the stale-
file case in more detail than this file does.*
