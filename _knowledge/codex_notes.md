# Codex notes: the turn-based exchange with Claude

Written 2026-09-13. These notes describe Jonathan's live file-based collaboration between Codex and Claude while building phases 1 and 2 of Cle. They cover observations through Codex's review of Round 10. Round 11 had not arrived when these notes were prepared.

This is operational evidence from one collaboration, not a benchmark of either model. Recommendations below are distinguished from the protocol Jonathan actually authorized.

## What we were trying to accomplish

Jonathan wanted Claude to implement the personal-assistant plan and Codex to review the implementation, with a back-and-forth until phases 1 and 2 were complete or personal intervention was necessary. Codex's role in this exchange was primarily independent review, local verification and explicit feedback. Claude owned the implementation changes.

The agents were separate sessions coordinated by files. Codex did not spawn Claude as a subagent, send it collaboration-tool messages, or start its CLI. Updating the agreed handoff file was the communication channel. Both sessions had to remain active and watch their incoming file.

This distinction matters for Vibeguild: writing a message does not itself guarantee the recipient is running, has seen it, or has begun work.

## The protocol Jonathan actually authorized

The coordination directory was:

`C:\Users\black\Jonathan\DEV\non-git\SPARK_PLAN`

- Claude writes `claude_to_codex.md`.
- Codex writes `codex_to_claude.md`.
- A new incoming handoff transfers the turn to its reader.
- The reader reviews and acts, then publishes its outgoing handoff.
- Once that handoff is published, its author stops project work and monitors the incoming file.
- Only one agent owns the project turn at a time. The other waits.
- Codex may stop monitoring after one hour with no response.
- The agents may also stop by mutual agreement.
- They should stop for necessary personal intervention rather than invent consent or personal preferences.
- Jonathan can stop, resume or steer the exchange directly.

An initial filename typo, `claude_to_code.md`, was explicitly corrected to `claude_to_codex.md`. It was important to settle the exact filename rather than monitor both indefinitely.

The one-hour rule was a no-response waiting limit. It did not establish a model-runtime timeout, a mandatory one-hour work allocation, or a heartbeat-based extension policy. We treated each outgoing handoff as the start of the next response window; an explicit user resumption could start a fresh window.

"Wait" meant no additional Cle implementation or review while Claude owned the turn. Jonathan subsequently explicitly asked Codex to write these notes while waiting; that authorized this separate documentation task without transferring the Cle project turn.

## What a working turn looked like

1. Read the complete incoming file.
2. Record its round, content hash and modification time.
3. Check its claimed changes against the implementation and the established requirements.
4. Run checks appropriate to the change. Use independent reproductions where existing tests miss an important boundary.
5. Write a complete outgoing response stating what was verified, what remains wrong, and what the next actor should do.
6. Publish the response atomically.
7. Start the response deadline and immediately arm monitoring.
8. Do no more project work until another complete incoming handoff arrives.

The files used headers such as:

`Status: Round 10 complete. Codex owns the next turn.`

and ended with an explicit handoff marker. Codex replies named the round reviewed and included the incoming SHA-256 hash. This helped distinguish a new reply from a stale file that still said "Codex owns the next turn."

That stale-file case happened on resume: the incoming Round 8 file still assigned the turn to Codex, but Codex had already reviewed it and published a Round 8 reply. The outgoing file's matching round and inbox hash established that Codex should wait, not review the same round again.

## Monitoring implementation and its limits

Codex checked both SHA-256 content hash and UTC modification time. A changed file was read in full; an unchanged file meant keep waiting. Monitoring used short sleeps, usually 45 seconds, followed by a check. This kept the session interruptible and avoided a single long blocking wait.

The outgoing response was written to a temporary sibling, `.codex_to_claude.pending`, then moved over `codex_to_claude.md`. Publishing only after the response was complete reduced the risk that Claude would react to a half-written message.

The complete-message marker was useful human-readable evidence, but our monitor did not enforce it as a parser rule. Similarly, hash/mtime detection is not a full delivery protocol:

- An editor touching a file without changing the message can look like an update.
- A non-atomic writer can expose partial content.
- Replacing the same two files loses historical versions.
- A sender cannot tell from publication alone whether the recipient consumed it.
- A restarted session may lose its in-memory "last seen" state.

The JavaScript orchestration store was convenient for the current round, digest and deadline, but it did not survive every resumed turn. We rebuilt state from the actual handoff files and conversation history. It should not be Vibeguild's durable source of truth.

## Sleep, missed watches and timing corrections

Jonathan explained that the laptop had gone to sleep, delaying Claude's update. An inactive machine is different from a slow model, a dead recipient, or a protocol deadlock.

Claude also reported failing to arm its watch after publishing, leaving a Codex reply unread for roughly twelve minutes. That was a watcher-lifecycle failure. An outgoing message must be followed immediately by a functioning wait; merely announcing "I am waiting" does not establish it.

One timing assertion in a handoff was incorrect. The concrete file times were:

- Codex's Round 6 reply: 2026-09-13 18:40:23 UTC.
- Claude's Round 7 handoff: 2026-09-13 19:30:04 UTC.
- Elapsed: about 50 minutes, inside the one-hour window.

Claude had described that resumed round as an overrun, then corrected the claim. The earlier overnight delay was explained by laptop sleep. We used timestamps to correct the record rather than accept the narrative.

This is a strong reason to store machine-readable send, receive and deadline events. Agents should not have to reconstruct elapsed time from prose or infer failure from silence.

## What status.md was, and what it was not

Claude introduced `status.md` as an informational heartbeat. Its motivation was to avoid a long work turn outlasting a recipient's waiting window. It proposed a way to signal ongoing work without handing the turn back.

Jonathan had not authorized heartbeat updates to extend the one-hour deadline. Codex therefore treated status.md as informational only:

- It did not transfer the project turn.
- It did not authorize the waiting agent to start project work.
- It did not reset Codex's deadline.
- It did not override either handoff file.
- It did not replace an actual response.

Jonathan later asked why the file existed; Codex explained this distinction. No new heartbeat policy was adopted.

For Vibeguild, separate **message delivery**, **turn ownership**, **liveness**, and **deadline policy**. A heartbeat can show that a process is alive without proving useful progress, receipt of a specific message, or permission to extend a deadline. An agent-created status file must not silently become a new coordination authority.

## What made the reviews useful

The useful division was implementation plus independent verification. Codex did not simply paraphrase Claude's implementation report or ask for more tests in general. The strongest feedback supplied:

- The specific operation or interleaving that failed.
- The observed result.
- The intended invariant.
- A small reproducible fixture.
- A bounded next change.
- A clear distinction between accepted work and unresolved work.

A practical handoff structure emerged:

1. Round and actor.
2. Changes claimed and checks actually run.
3. Findings, with reproductions.
4. What is accepted.
5. What remains untested or deferred.
6. The next coherent implementation slice.
7. Whether to continue, stop, or request personal intervention.

The review should not turn every concern into a fresh architecture project. After accepting the calendar simulation repairs, Codex explicitly asked Claude not to rework those details and to ship public-task continuation. Continuation had been deferred twice; a bounded, working slice was better than repeatedly restating its requirements.

## Passing tests did not establish the claimed properties

The app suites grew as the exchange progressed:

| Reviewed round | App tests passing in Codex's environment | Important remaining finding |
| --- | ---: | --- |
| 7 | 165 | Calendar duplicate execution/ownership boundaries and a cancellation race |
| 8 | 188 | Missing calendar migration, time validation, startup cleanup coverage |
| 9 | 207 | A finally block erased cleanup ownership before the outer handler read it |
| 10 | 227 | Conversation durability, immediate-follow-up admission and delivery atomicity |

These counts measure executed tests, not production readiness. The runner's unchanged 91-test suite was not repeatedly rerun in later reviews.

Several instructive failures:

### Assertions in comments were mistaken for guarantees

Claude added a set tracking whether an attempt had spawned a process. Its error-handler comment said that a failed terminal write would retain that fact. An unconditional finally block discarded it anyway. The outer handler then recorded cleanup as verified even when termination had been unverified.

A direct reproduction through the real worker loop observed cleanup arguments `[False, True]`, a terminal row with `unresolved=False`, and admission of the next task. Existing tests had called an inner method and checked that an unchanged RUNNING row blocked admission; they never reached the outer handler where the false-clean transition occurred.

The lesson is to test the boundary named by the claim. A test name or explanatory comment is not evidence that the important interleaving was exercised.

### Fixing one instance did not fix the defect class elsewhere

The task database received an additive migration, but the new calendar session_id initially only appeared in CREATE TABLE IF NOT EXISTS. Existing calendar databases therefore opened but failed on new proposals. A populated old-schema fixture exposed it.

A shared-store or migration change deserves an old-data path, not just a clean-database test.

### A feature changed assumptions in previously repaired lifecycle code

Conversation continuation allowed a COMPLETED task to become QUEUED again. The worker still decided whether an attempt had settled by reading the task's current terminal state. A follow-up inserted immediately after completion caused the worker to retain the old attempt as unsettled and refuse further work.

The new user interaction invalidated the old identity assumption: **a conversation/task is not the same thing as one execution attempt**.

### Preserving UI appearance was not preserving history

A fallback displayed an old task's answer when it had no conversation rows. Its first follow-up nevertheless sent only the new message to the model. The next result replaced the legacy answer, and the fallback disappeared.

Checking that a page renders an old result is not a migration test for the full follow-up lifecycle.

### Correct individual writes did not make the operation atomic

Appending an assistant answer before the conditional completion write let a cancelled task show an answer as delivered. Creating a task and its opening turn in separate autocommitted writes let an opening-turn failure leave executable queued work behind.

The test needs to fail between writes, not just inspect the happy-path final rows.

## How to make tests efficient in an agent exchange

Use real processes when the property is actual process containment or termination. A fake that says "killed" does not establish that a child stopped doing work.

Use synthetic handles and temporary SQLite when the property is a state-machine or persistence interleaving. This makes failure injection deterministic without unnecessarily launching or killing processes.

Useful injection points in this exchange included:

- PID persistence after a process started.
- Cancellation during audit or immediately before conditional completion.
- The first terminal write failing while a later one succeeds.
- A follow-up landing immediately after completion but before worker release.
- An insert failure between task creation and opening-turn creation.
- An old database with populated records.
- Two callers trying to execute the same approved calendar proposal.

One appropriate full test run plus focused reproductions was usually enough. Repeating an unchanged green suite did not add much evidence. No paid model calls were necessary for these implementation reviews.

## Evidence, evaluation and model-selection discipline

A provisional harness choice is not a model-quality verdict. Earlier work provisionally favored Claude's tested integration path; it did not establish a scored Astra-versus-Claude quality win.

Synthetic research tasks exposed sourcing and calibration problems, but did not establish whether Jonathan would actually use Cle or how much correction it would require. Existing cases should not be repeatedly rescored after being read and tuned against.

The agreed personal-use protocol was:

1. Preserve the user's real brief, constraints and desired endpoint.
2. Retain the first answer unchanged.
3. Ask whether it was usable as-is, and record the user's reason.
4. Distinguish legitimate clarification, changed preference and corrections caused by an error or omission.
5. Record corrective turns, approximate active checking/fixing time, whether the user redid the task, final acceptability, elapsed time and the actual usage/cost basis.
6. Do not invent counterfactual "minutes saved" or claim a universal model ranking from a few cases.

Continuation supports this measurement, but it was wrong to say correction burden was literally unmeasurable without an app feature. A manually maintained public conversation can bridge an initial pilot.

## Authority and stopping boundaries

The direct user's instructions remained authoritative across handoffs. For example:

- Research and prepare, then approve.
- Push-to-talk on phone/laptop.
- Every calendar create, edit and delete shown for approval first.
- Initial spending limits were provisional.
- Stop or resume monitoring when Jonathan says so.

An agent quoting or summarizing the user's preferences is useful context, but it should not replace the original instruction if they conflict. Code comments, plans and status files do not create new user authorization.

Communication authorization was specific to this exchange. It did not imply authorization to send email, connect private accounts, make purchases, deploy, or perform real calendar writes. The reviews used local fixtures and a simulated calendar.

"Needs Jonathan" also needed discipline. Authentication code, voice UI and speech adapters were implementation work we could do. Account consent, target-device access, private-network provisioning and actual personal-use feedback were separate dependencies. Do not hide unfinished implementation behind a request for personal intervention.

Stopping should mean one of:

- The authorized objective is actually complete.
- Necessary personal intervention prevents meaningful further authorized work.
- The user explicitly stops the exchange.
- The agreed no-response window expires.
- Both agents explicitly agree to stop within the task's scope.

Test counts, elapsed effort, or one accepted subsystem were not evidence that phases 1 and 2 were complete. As of this note, Phase 2 was still in progress.

## Recommendations for Vibeguild -- not changes already adopted

### Make coordination a small durable state machine

Keep separate records for:

- Session/run identifier.
- Message identifier and sequence.
- Sender and recipient.
- In-reply-to identifier.
- Turn owner.
- Published and received timestamps.
- Last consumed message identifier.
- Deadline and the policy that set it.
- Explicit paused/stopped/awaiting-user states.

Persist them. An in-memory watcher variable or a prose header should not be the only record of who acts next.

### Preserve messages instead of overwriting all history

Use immutable, numbered message artifacts plus an atomic pointer to the latest complete message. Archive the actual review and the corresponding implementation revision or change manifest.

Our two-file system worked as a minimal interface, but recovering earlier history required conversation context and hashes. Immutable messages would make restart, audit and duplicate detection much simpler.

### Separate ownership from delivery acknowledgment

A message can be published, received, accepted and completed at different times. Record those states separately. Acknowledging receipt should not itself transfer the turn or invite simultaneous project work.

Arm the receiving watch as part of the send transition. Avoid a design that depends on the model remembering to run another watch command after announcing completion.

### Treat "exactly once" as a processing property, not a filesystem event

Filesystem changes can repeat. Use message IDs and reply relationships to recognize duplicate delivery, and make processing idempotent. Content hashes help integrity and deduplication; modification times alone do not establish a new logical message.

Require a complete envelope or atomic publication before processing. Our end marker was helpful, but a structured completeness rule would be better.

### Define timeout and heartbeat semantics explicitly

Specify whether timeout means wall-clock silence, active-machine elapsed time, absence of acknowledgment, or absence of a complete reply. Decide what suspend/resume does.

If heartbeats extend a deadline, make that an explicit user-approved setting, record the extension, and bound it. Keep "alive" separate from "made progress" and "owns the turn."

The observed protocol kept the original deadline; it did not adopt these extensions.

### Support pause/resume as a first-class operation

On resume, inspect durable message/reply state before acting. Do not process an already-answered incoming file just because its old header still grants the turn.

A user's direct pause should interrupt monitoring promptly. Resume should clearly state whether it restarts the wait window or continues an existing one.

### Preserve authority and scope

Treat handoff files as task communication, not system policy. Distinguish facts, requests, direct-user preferences, proposals and uncertain claims. Escalate only a specific missing permission or decision, after making the result concrete enough to review.

If two actors share a worktree, ownership needs an explicit coordination rule. A status dashboard alone does not prevent simultaneous edits. Do not introduce a stale lock that can only be cleared by guesswork after a crash.

### Keep waiting quiet and observable

Our monitor emitted frequent "still waiting" commentary because this environment requested frequent updates. It was repetitive and conveyed little new information.

A product should show a persistent waiting indicator, current owner, last message, last heartbeat if supported, and deadline. Notify on receipt, timeout, stop or a substantive change rather than repeatedly adding identical chat messages.

### Optimize for useful progress, not debate length

A good round resolves concrete uncertainty or delivers a coherent slice. Record accepted findings so they do not keep returning as generic concerns. Carry unresolved findings forward with stable identifiers and explicit closure evidence.

Independent review earns its cost when it finds an actual failure, verifies an important property, or improves the next implementation decision. Repetition, narrative agreement and escalating test counts by themselves are not progress.
