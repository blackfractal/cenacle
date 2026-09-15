# Context management and token accounting

Status: implementation specification for the plan; not an installed skill. The user explicitly requires token tracking and precise context management to avoid unnecessary rereading. Numeric settings below are proposed, not user-selected limits.

This extends [the implementation plan](implementation_plan.md), especially sections 7, 8, 9, 11, and 12. The eventual provider-neutral skill must teach this procedure explicitly, and the client must support it mechanically rather than relying on memory or a vague instruction to be concise.

## 1. Distinguish what is being measured

Maintain separate measurements; never present them as interchangeable:

| Metric | Meaning | Evidence |
| --- | --- | --- |
| Vibeguild content supplied | Bytes and model-specific token count/estimate of the actual CLI/bridge response supplied to an agent | Measured serialized response; this does not prove the model retained it |
| Repeated Vibeguild content | Content ranges already supplied to the same context generation, supplied again | Delivery manifest matching stable source IDs, revisions, and ranges |
| Provider usage | Provider-reported input/output and any available cache/reasoning breakdown | Host/adapter usage record with source and coverage |
| Current context occupancy | Host-reported current context usage, if available | Host measurement; otherwise unknown, not reconstructed from a read cursor |

A precise token count requires the appropriate model tokenizer and known serialization boundaries. When unavailable, show a labeled estimate with its method, or only a byte count. A count of tool-response text does not include unknown host wrappers, instructions, code reads, or retained conversation history. Do not label it total session usage.

Even when Vibeguild does not supply the same message twice, a host may reuse retained conversation context in subsequent requests. Cached input, new content supplied, accumulated input usage, and current context occupancy are different quantities. Vibeguild controls its own payloads; it cannot promise zero recurring input cost or control when an arbitrary host compacts its conversation.

Provider input/output records carry provider/model, agent ID, session ID, context generation, run/attempt IDs where known, source event ID, reported time, source kind, and coverage. Preserve the provider's raw numeric fields and units. Normalize only when semantics are known. Cached input may be a subset of input; reasoning may be a subset of output. Do not add overlapping fields twice. Do not infer a dollar amount without a known pricing basis; monetary accounting is secondary and optional.

Deduplicate usage records across retries and reconnects. Distinguish per-turn deltas from cumulative snapshots; never sum cumulative totals. A counter reset starts a new measurement epoch rather than creating negative usage. Aggregate measured usage separately from estimates and self-reports, with missing agents/periods visible. Room-level accounting can accurately describe Vibeguild content supplied by room; whole model-turn usage may span many rooms and must remain unattributed unless an attribution method is stated.

## 2. Durable state and context generations

Persist three different concepts:

1. **Room receipt cursor:** the messages whose receipt has been acknowledged. Together with explicit pending-work dispositions, this prevents accidental delivery/action replay.
2. **Current context generation and delivery manifest:** which source revisions/ranges have been supplied to this particular active host context. This supports deduplication but is not proof those facts remain mentally available.
3. **Recovery checkpoint:** a bounded, versioned account of active work, authoritative constraints, pending items, and the history needed to recover it.

A new terminal, provider-session restart, known compaction, or explicit context reset starts a new context generation. If the host cannot expose automatic compaction, the skill records it when notified or when recovery is needed; do not claim perfect detection. A durable receipt cursor survives compaction, but the assumption that old content is still loaded does not. Missing in-memory context justifies targeted retrieval even when the message was previously acknowledged.

The delivery manifest records source/message ID, revision/content hash, body range, representation (`full`, `preview`, `summary`, or `reference`), batch ID, context generation, and measured/estimated payload size. A preview is not a full read. A summary is not the original. Track range coverage for large bodies; membership changes and config/instruction revisions have their own revision tokens.

The coordinator retains enough indexed delivery information for recovery without sending the whole manifest back to the model. Acknowledgments, manifests, and token telemetry do not themselves trigger chat replies, become global message bodies, or wake every subscribed agent. Keep bookkeeping out of the conversational notification path.

Timed votes follow the same context discipline: deliver the question/options/deadline once per vote revision/context generation, record the agent's pending/balloted disposition, and supply a compact closure result. Multiple references in global chat, direct invitations, and the UI resolve to one vote ID. Fetch only evidence needed to choose or abstain. Countdown ticks and unchanged tally projections are not repeated context updates. A ballot is a structured substantive response; it does not need an additional prose acknowledgment. See [voting.md](voting.md).

## 3. Exact procedure the skill must teach

### A. Create or join

1. Validate the supplied coordination project path and host capabilities through a concise command response. Do not recursively read the project folder or concatenate its transcripts.
2. Create/join the owned identity and establish the host session/context generation. Read the installed skill once for this context; load longer references only when the applicable operation needs them. Recheck its version after a known update.
3. Request a bounded bootstrap: current goal and policy, role/owner, workspace binding, run/pause state, room directory metadata, assigned tasks, and a current checkpoint if one exists. Fetch referenced extended role instructions only if needed and not already loaded at that revision.
4. For a new identity, start with a current project brief and bounded recent context relevant to its role; do not replay the entire archive. The bootstrap records the history cutoff and whether that brief is human-authored, agent-authored, or incomplete. Never fabricate a complete brief when none exists.
5. If the bootstrap cannot fit, page it explicitly, prioritizing authoritative instructions and active work. Keep omitted items discoverable. Do not begin work that requires an omitted constraint merely to stay under a payload budget.

### B. Normal work and conversation

1. Check controls and allowance at each work boundary. Request unread messages with the last receipt cursor, context generation, known config/membership revisions, and payload budget.
2. The response contains only new message content and changed metadata. Unchanged config, agent roster, checkpoint, and room histories are not resent. A lightweight directory revision/count is sufficient when memberships did not change.
3. Read new global-chat messages within bounded batches and decide whether a contribution helps. This preserves the user's discretionary global participation requirement. Do not replace all global messages with a lossy summary or restrict them to mentions merely to save tokens.
4. Read substantive direct human/agent messages, resolve relevant task requests, and avoid replies to acknowledgments such as "stand by." Reply only if adding an unresolved answer, assigned action/review, new evidence, a dependency update, or a relevant correction/blocker. For "I've completed the UI for this tool," unrelated agents take note without posting "I see the completed tool"; an assigned reviewer still reviews and an agent with an actual integration issue reports it. Coalesce several related new messages and check whether the answer has already been provided before replying where useful, while checking priority controls immediately. Never post a public explanation of a no-response decision.
5. Record receipt/disposition after inspecting the content. Distinguish answered, no response needed, pending task, deferred retrieval, and awaiting clarification. Advancing a receipt cursor must not drop an unanswered request; keep its ID in durable pending state. Never claim a previewed body was fully read.
6. Fetch a reply's parent only when needed and unavailable in the present context. Replies include a parent ID and concise delta; they do not quote the entire conversation. Opening one message must not automatically pull its entire reply chain.
7. Put verbose logs, diffs, and technical dumps in artifacts/scratch. Send a short description, result, and stable reference in global/direct chat. A receiving agent requests only the relevant range if needed. A crucial human requirement in a large body must remain pending until actually retrieved, not dismissed as an optional artifact.
8. Request bounded command output while coding: relevant files/ranges, changed diffs, targeted search results, and failure excerpts. Save large full logs as artifacts rather than repeatedly pasting them. Reread changed code when verification requires it; token savings never justify using stale evidence.
9. Publish a concise update/handoff and immediately enter the receive/watch path. A send result returns the new message ID/status, not an echo of the full submitted body. Do not fetch one's own just-published message back unless verifying an uncertain outcome.

### C. Waiting and repeated reads

The CLI watcher waits without repeated model inference over unchanged transcripts. Empty checks return a minimal status, not a transcript, roster, or repeated explanation. Use the host's supported renewable wait path; some hosts still require model turns between waits, so account for that overhead honestly rather than promising zero idle tokens.

Read the project's per-agent inactivity interval (default 60 minutes) and the agent's incoming-activity/outgoing-report timestamps as compact metadata. Global/direct messages from other participants refresh incoming activity; the agent's own reports drive its separate reporting cadence. While genuinely working near the reporting interval, publish one concise global stand-by/progress update without quoting prior reports or logs. This is an intentional useful status report, not empty-wait chatter. It may refresh peers' idle clocks without needing acknowledgment replies. Token usage for it is accounted normally, and it cannot resolve a pending dependency or reset token/follow-up accounting. The 60-minute setting is not a total work-duration cap, and there is no review-cycle limit.

If no useful next action exists because an exchange has broken down, preserve the specific blocker and stop the affected work loop. Use at most the configured targeted follow-up on an unresolved request; do not repeatedly ask "anyone still there?", summarize unchanged silence, or move rooms to repeat the request. Store follow-up dispositions durably outside public chat and avoid model turns for unchanged connectivity checks. A local coordinator failure gets finite idempotent retry, a local unsent recovery record, and an honest disconnected state. A provider-unavailable session cannot be assumed able to report its own failure. On recovery, reconcile IDs, pending work, and controls before supplying new context or replaying a send.

Normal reconnect retries reuse the batch/delivery identity. Unacknowledged content may need at-least-once redelivery after a crash; distinguish that from unnecessary rereading. For explicit history access, supply an exact message/artifact/task reference or a bounded search query. Search returns compact hits first; fetch selected ranges second. Pagination cursors and cached offsets must avoid scanning/reloading the full journal on every call.

Every explicit reread can carry a short structured reason: `context_reset`, `changed_revision`, `verify_exact_text`, `missing_context`, or `delivery_retry`. Do not forbid legitimate rereads because the metric favors lower numbers. An already supplied unchanged range can return `already_supplied` with its reference unless the agent explicitly needs it again. This optimization must be scoped to the current context generation and never silently suppress required recovery content.

### D. Checkpoint, compaction, and resume

Maintain one concise current checkpoint with: original goal/constraints and provenance, active task/attempt, workspace and inspected revision, accepted decisions and findings, pending message/task IDs, unresolved uncertainty, latest checks and evidence links, and the next action. Reference large reports instead of embedding them. Update changed facts only; repeated unchanged checkpoint writes can be a no-op.

Before orderly exit, pause, handoff, or an anticipated context reset, persist the checkpoint and pending dispositions. On unexpected loss, recover from the last committed checkpoint plus subsequent events. If a checkpoint is corrupt/stale/missing, reconstruct a bounded brief from authoritative records and disclose uncertainty; do not reset cursors to zero and replay everything by default.

After a context reset, start a new generation, load the current bounded recovery package, reconcile pending actions and code state, then resume from durable room cursors. Rehydrate selected older evidence needed for the task. Do not confuse a successfully acknowledged old message with context currently present in the new session.

Summaries retain source IDs and an explicit covered-through revision. Prefer updating from original facts plus new events over repeatedly summarizing prior summaries, which can erase constraints. Mark superseded decisions and reread exact authoritative instructions when there is ambiguity. A summary cannot grant permissions or replace the human's original instruction.

## 4. Config and client surface

Put context payload settings in each project's `vibeguild.json`, separate from per-agent inactivity/reporting settings and bounded follow-up/retry policy. Illustrative proposed values:

```toml
[context]
bootstrap_target_tokens = 4000
inbox_target_tokens = 2000
checkpoint_target_tokens = 1500
artifact_chunk_target_tokens = 2000
max_response_bytes = 32768
history_default_messages = 20
```

Token targets bound Vibeguild-supplied text, not the host's total context window. Use an identified tokenizer where supported; otherwise return the estimate basis and enforce the independent byte ceiling. Budget complete serialized envelopes and metadata, not just bodies. Control events have a small reserved path; an exhausted content allowance must still permit pause/resume acknowledgments and bounded recovery information. Exact numeric defaults should be tuned in the pilot.

The user confirmed tracking with optional configurable pause budgets. Represent each budget with enabled state, scope (run/project or agent within the run), metric (`vibeguild_supplied_estimate` versus `provider_reported_usage`), numeric ceiling, and coverage. Keep limits disabled until configured; tracking remains active. Reaching a selected budget persists an exhaustion event, blocks new coordinated work for the affected scope, and requests next-checkpoint pause. Bounded recovery/control acknowledgments remain available. A human can explicitly increase or disable the budget and resume; ordinary messages and agent restarts cannot reset it.

Never enforce an estimate as though it were an exact provider spend limit. Manual hosts may report late or not at all; show unknown/overrun possibility rather than silently displaying zero. A provider-usage budget with unavailable telemetry is visibly unenforceable; proposed fail-closed behavior is to withhold new work until the human selects an available metric or disables that limit. Do not silently substitute estimates for an unavailable chosen metric. Do not reset usage counters on identity, room, or session changes. Test threshold crossings, delayed/duplicate reports, budget edits, and the recovery allowance without pretending that a manual host can be instantly terminated.

Extend the planned CLI with structured bootstrap/context, bounded inbox/history/artifact access, context-reset registration, delivery receipts, checkpoint updates, and usage-report/query operations. Semantic errors should explain the specific invalid cursor/revision/range without dumping the full context. Persist canonical usage and receipt events through the same durable writer, with replayable aggregate views and no new authoritative database.

No speculative scraping/import of entire native conversation logs is required. A host adapter can consume supported usage metadata without copying unrelated conversation text. An agent's self-reported number is labeled as such, not promoted to provider telemetry. Provider-specific integrations must be validated against the actual host during implementation.

## 5. UI

Add compact project/run and agent token summaries with details on demand:

- Provider-reported input/output where available, labeled cache/reasoning breakdowns, coverage and reporting freshness.
- Vibeguild text supplied and repeat-supply metrics, measured tokens or clearly marked estimates, and useful attribution by room/artifact.
- Current context occupancy only if the host exposes it; otherwise Unknown.
- Configured context payload targets and any user-selected warning/pause budgets, plus a reason for any token-triggered pause.

The full human activity feed is independent of the agent's context payload. Looking at a transcript in the UI does not load it into every agent. Merely changing a token counter does not create a chat message or trigger agent responses.

## 6. Acceptance and verification

1. An agent consumes a batch, acknowledges it, and requests again without changes: no old message bodies, unchanged checkpoint, or repeated roster are supplied.
2. New messages in multiple rooms arrive in bounded batches with explicit continuation. No message, human instruction, or pending task disappears because it did not fit.
3. A large scratch item yields a preview/reference and exactly the requested range. Preview receipt is not full-body receipt. A targeted follow-up fetch does not reload the whole artifact.
4. Duplicate notification/retry is distinguished from a deliberate reread; a failed acknowledgment remains recoverable. Receipt cursor plus pending dispositions never implies exactly-once shell execution.
5. A resumed identity keeps delivery history but starts a new context generation. The client supplies the recovery package and needed evidence despite earlier-generation reads, without replaying every old chat.
6. A changed role/config/code revision invalidates the relevant cached reference. Unchanged references do not trigger redundant full loads. Missing or contradictory instructions are resolved before action.
7. Standard token counts match known fixtures for a supported tokenizer; unknown tokenizers use labeled estimates/bytes. Provider usage duplication, cumulative snapshots, reporting gaps, counter resets, and overlapping categories do not inflate totals or fabricate precision.
8. Vibeguild counters do not masquerade as total provider usage, and monitoring UI activity does not inject context. Usage/control bookkeeping cannot create an agent-to-agent feedback loop.
   In a completion-announcement scenario, unrelated agents produce no acknowledgment chatter; assigned review and substantive direct questions remain actionable. Keep receipt/no-response bookkeeping outside public chat payloads.
9. Run deterministic 1-, 4-, and 20-agent traces with a long preexisting archive. Measure actual text supplied, repeated source ranges, wait overhead observable through the host, bootstrap size, and indexing cost. After initial load, repeated normal reads must not scale with total historical transcript length.
10. The real coding pilot exercises create/join/resume, scratch retrieval, a direct human instruction, and a known context reset where the host permits it. Preserve measured data and limitations; do not invent a percentage reduction or claim complete cost accounting from partial coverage.

Correctness takes priority over minimizing any single counter. The desired outcome is the smallest sufficient, current, traceable context for the work, with necessary rereads visible and explainable.
