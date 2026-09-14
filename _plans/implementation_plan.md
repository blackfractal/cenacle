# Cenacle implementation plan

Status: implementation authorized by the user and v0.1 built. This document preserves the longer design; [implementation_status.md](implementation_status.md) records delivered behavior and remaining acceptance work.
Date: 2026-09-13.

## 1. Product and intended outcome

Cenacle is a local, folder-based collaboration workspace for a human and several independently started coding agents. The human opens a project in a polished chat UI. Codex, Claude, ChatGPT, and other capable agent hosts use a provider-neutral skill and a supported project-access client to identify themselves, exchange messages, coordinate coding work, and recover their project understanding after a session ends.

The first successful workflow is real coding work: Jonathan starts an implementer and a reviewer, gives them a bounded goal, observes their conversation, interjects from the UI, and receives a verified result or a precise explanation of why work paused. A third agent can join without reconfiguring the whole system. The collaboration must survive a session restart without silently losing messages or repeating completed actions.

Planning output belongs in `_plans`. Questions and undecided defaults are recorded in [discovery_questions.md](discovery_questions.md). Recommendations below are proposals, not recorded user decisions.

## 2. Requirements already established

- A project is a normal folder with a legitimate top-level `cenacle.json` and a `cenacle_files/` directory.
- `cenacle.json` identifies the project, human participants, their agents, agent identities, and roles. It contains the overarching goal and a general_context section all agents read on joining/resuming and when changed.
- The app starts with an open-project experience and validates the selected folder.
- `agent_chat` is the main global chat; `agent_scratch` is a separate stream for longer technical material.
- The human can send messages, mention specific agents, see agent-to-agent conversations, and interject in them.
- Each agent has visible personal working notes and a place for direct human conversation.
- Agents know their chat memberships, consume new messages without repeatedly loading old history, and can deliberately retrieve earlier material.
- Identities and useful project context survive terminal/session loss. An agent can resume an identity, register a new identity, or initialize a project expecting others to join.
- The first version assumes one human owns all agents. Human ownership must remain explicit so multiple humans and remote workstations can be added later.
- Finite collaboration is a core requirement. The system must not rely on endless polling, endless review, or model agreement as its completion criterion.
- The skill is reusable by other people and agent hosts, with explicit create-project, join-existing-project, and resume-identity workflows. It must not assume Jonathan, this repository, or a fixed provider pair.
- Agents may work autonomously within a scoped task; they ask before destructive or external actions.
- V1 coordinates sessions the human starts independently. It does not launch or manage agent sessions.
- Agents decide whether global `agent_chat` messages merit a response. Substantive direct messages from humans or agents normally deserve a response; informational acknowledgments such as "stand by" do not require one.
- Safety settings live in each project's `cenacle.json`. The clarified 60-minute default is each agent's incoming-chat inactivity interval, not a work/run duration cap. While still working near an hour since its own last report, an agent posts a brief stand-by update. There is no review-cycle limit; breakdown detection and bounded follow-up behavior must work for agents whose tasks never involve reviews.
- The human can pause/resume all agents or individual agents from the UI, independently of the terminal interfaces. V1 pauses at the agent's next checkpoint. A separate immediate-pause control is a possible future feature, for both individual and project-wide control.
- Each agent tab separates visible working notes/decisions/blockers from the direct human-agent chat.
- V1 targets Windows only; keep macOS, Linux, and WSL support feasible through isolated platform-specific code.
- The Cenacle project folder is separate from the code workspace and points to an external location. Supporting several repositories in one project remains an open scope detail.
- Support one agent as the minimum, 3-4 as typical, and about 20 as the initial upper sizing target, with room to grow. Twenty is a capacity target, not a hardcoded identity limit.
- Agents may create profiles, group chats, and tasks without asking each time. These creations must be clearly visible in the UI, including a complete list of ongoing chats that the human can open as separate tabs.
- The user permits structured text, including JSON, and leaves the storage pattern to the implementation design. Free-form, directly appended chat files are not required.
- The UI has three complementary views: a combined activity feed showing updates across all chats, an All Chats list where double-click opens a conversation in a new in-window tab, and a separate Open Tabs list for conversations the human is currently monitoring.
- Token tracking is a first-class requirement. The skill must teach a precise context-management procedure that avoids unnecessary rereading, with bounded incremental reads, revision-aware retrieval, and recovery across context resets. Distinguish measured usage, estimates, and unknown coverage.
- The visual direction is a sleek, high-tech interpretation of Discord/Slack. Agents have distinct, stable accent colors and prominent short names; every agent also has an immutable UUID within the project.
- The skill teaches selective responses: a completion announcement does not warrant acknowledgment replies from every agent. Reply when contributing useful new information, answering a substantive request, or fulfilling an assigned responsibility.
- Code editing uses separate Git worktrees by default, with a shared-directory fallback for sequential work.
- Token usage is tracked, with optional configurable budgets that pause work at the next checkpoint when reached. Budgets explicitly identify their measurement basis and coverage.
- Keep the skill provider-neutral; a specific ChatGPT integration is deferred and is not a first-release dependency.
- Agents recognize stalled or broken collaboration and checkpoint/pause rather than repeatedly asking whether anyone is still there. V1 runs on one machine; preserve the architectural path to agents collaborating from different machines later.
- Agents can create timed advisory votes in chat for the project's agents and the human. Votes have explicit options plus Abstain and close at the specified deadline or early when every invited agent and the human have submitted a ballot. If the human has not voted, keep the vote open until their ballot or the deadline. Missing responses are not abstentions or agreement; agents use judgment when acting on the recorded result.
- V1 has one designated lead per project, with final say among agents on disagreements within the authorized project scope. The human retains final authority. A lead council is deferred.
- The user subsequently authorized building both the UI and portable skill; see the implementation status for the release boundary.

## 3. Proposed first-release scope

Deliver a local coordinator service, browser UI, CLI, shared skill, example project, and setup guide. V1 uses manually launched agent sessions, as confirmed by the user; retain an adapter boundary for a possible future managed mode. Windows is the only required v1 platform. Isolate path resolution, filesystem watching/locking, browser/folder launching, and any future process control behind small platform interfaces so macOS, Linux, and WSL can follow without rewriting the protocol. Cross-platform execution is not a v1 acceptance claim.

Include global chat, scratch chat, agent-to-agent rooms, per-agent human chat and notes, a combined activity feed, a complete ongoing-chat list with double-click-to-open tabs, a separate Open Tabs list, visible agent/task directories, mentions, project/agent creation, incremental inbox reads, durable recovery, basic last-seen reporting, task claims, and bounded runs. The confirmed monitoring layout uses the feed, lists, and tabs; a tiled view is not part of v1 scope.

Timed advisory chat votes are also a v1 requirement. The protocol, UI, and skill behavior are detailed in [voting.md](voting.md). Early closure requires the human's ballot as well as every invited agent's; otherwise the poll stays open until its deadline. Results inform agent judgment rather than automatically selecting or executing work.

Defer remote networking, shared Internet hosting, account systems, encrypted/private rooms, native terminal embedding, voice, billing integrations, automatic provider/model selection, and automatic session relaunch unless answers make one of these essential. Multiple-human identifiers are present from the start; multi-user authentication is not pretended to exist.

**Release boundary:** the user accepts cooperative next-checkpoint pause for manually started sessions in v1. Cenacle enforces admission and message/task limits through its service; agents acknowledge the pause at their next work boundary. Show requested versus acknowledged pause rather than claiming an in-progress command has already stopped. Immediate interruption/verified process termination remains future adapter or supervision work.

## 4. Architecture

```text
Human browser UI ---- local authenticated API ----+
                                                 |
Agent skill -------- cenacle CLI -----------------+--> coordinator
                                                       |
                                                       +-- validates identities and commands
                                                       +-- serializes durable mutations
                                                       +-- enforces run/task policy
                                                       +-- emits resumable notifications
                                                       |
                                                       v
                                              normal project folder
                                              config + immutable events
                                              readable chat files
                                              agent recovery records
```

Use one coordinator writer per project on a local filesystem. The CLI can connect to the existing coordinator or start the local service when authorized to use the project. Closing the browser does not close the coordinator or agents. Shutting down the coordinator stops new coordinated work; clients report loss of connection and checkpoint at their next safe boundary.

Provisional technology direction: a Python core/CLI/local HTTP service plus a TypeScript browser UI. Keep business rules in the core, independent of HTTP and UI frameworks. Choose exact framework versions and packaging after the installation answer, targeting Windows first. Serve built UI assets from the same local service; the end user should not need to run a separate frontend development server.

A single TypeScript runtime is also viable if the user prefers Node-based installation. Do not implement both. No database is required as the authoritative store; a search index may be disposable and rebuildable if profiling later justifies it.

Browser updates use a resumable event stream, with ordinary HTTP commands for writes. Files remain the durable collaboration record. Filesystem notifications are hints; startup and reconnect reconcile against persisted event IDs. Coordination needs the service, but reading the project does not.

Size v1 for 1-20 active agents, with 3-4 as the ordinary case. Keep identifiers, storage, and memberships independent of that number. Twenty agents could form 190 distinct pair rooms, but create rooms only on demand. Maintain one project event subscription per client rather than a polling process for every pair. Page histories and bound inbox batches; the complete room directory must remain visible/searchable without loading every transcript or opening every tab. A configurable resource cap may be added, but do not silently interpret the sizing estimate as a fixed lifetime profile limit.

## 5. Project layout and configuration

The coordination folder is independent of the code repository. `cenacle open` selects this folder, validates its config, and resolves its external workspace binding; it never treats the coordination folder as the code working directory by default. Agent commands carry an explicit project path so they continue to find coordination state while working elsewhere. A missing code path should leave chats readable and explain why coding cannot proceed.

Proposed project layout (IDs abbreviated for readability):

```text
project/
  cenacle.json                         # versioned declarative project config
  cenacle_files/
    agent_chat.txt                    # readable generated global transcript
    agent_scratch.txt                 # readable generated technical transcript
    journal/
      000000000001_evt_a.json          # immutable committed event/envelope
      000000000002_evt_b.json
    chats/
      room_a/
        chat.txt                      # readable generated room transcript
    agents/
      agent_a/
        instructions.md               # optional extended role guidance
        notes.txt                     # visible working-note transcript
        direct_chat.txt               # human/agent room transcript
        checkpoint.md                 # current recovery brief, versioned by events
        state.json                    # rebuildable memberships, cursors, work state
        context.json                  # rebuildable context generation/delivery manifest
    artifacts/
      artifact_a/
        output.txt                    # immutable attachment/log/reference material
    state/
      project.json                    # rebuildable run/task/room state
      usage.json                      # rebuildable token/payload usage aggregates
      votes.json                      # rebuildable open votes, ballots, results
    runtime/                          # ignored machine-local endpoint/lock data
    cache/                            # disposable offsets/search data
```

Use UTF-8 throughout. Design choice, under the user's permission to choose an appropriate structured format: each journal record is one complete, immutable JSON file containing a versioned envelope and a Markdown body string (or a bounded bundle of related changes). Use standard JSON parsing/serialization rather than a custom text delimiter grammar. Newlines and code fences in bodies cannot accidentally terminate a record. Pretty-print envelope files for inspection; generated `.txt` transcripts present bodies naturally without JSON escaping. Freeze exact fields and schema validation in the protocol milestone.

The human-facing `agent_chat.txt` and other transcripts are real files, but they are projections of immutable records. Agents publish with the CLI rather than manually appending. The journal is authoritative for messages and operational transitions; transcripts, cursors, room lists, and indexes are reconstructible. A damaged projection never destroys the underlying conversation.

This design favors complete JSON records over a shared JSON Lines append log: each event has its own atomic publication boundary, so a partial append cannot corrupt a shared tail. The tradeoff is more small files, which the 20-agent/history checks must measure. Keep records behind a storage interface and add journal segmentation/indexing only when measured growth warrants it. Bulk exports may use JSON Lines; do not introduce a second writable message authority. Protocol writes belong to the CLI/service; manual edits to committed records or generated transcripts are unsupported mutations that validation should detect and report, not silently accept as new messages. Reconstruct transcripts from intact records, and use explicit linked correction events for intentional message changes.

The implemented top-level file is JSON. It includes `general_context`, which every agent reads on joining/resuming and when changed. Use the UI for live updates; offline metadata/policy edits are imported on reopening with a review pause. IDs and roster are managed by registration, resume and lead commands. The following is an example; the fuller layout above remains a design target (see implementation_status.md for actual projections).

```json
{
  "schema_version": 1,
  "project": {
    "id": "89bc7f3c-d371-44e6-a2c8-eaf06c7ac142",
    "name": "Example coding project",
    "goal": "Ship the agreed first milestone",
    "workspace": "C:\\code\\example-repo",
    "reference": ""
  },
  "general_context": "Shared background, conventions, constraints and key references for every joining agent.",
  "humans": [
    {
      "id": "3967669a-764b-4453-afb1-7065166abbd3",
      "name": "Human"
    }
  ],
  "agents": [],
  "lead_agent_id": null,
  "policy": {
    "agent_inactivity_minutes": 60,
    "working_status_interval_minutes": 60,
    "working_status_lead_minutes": 5,
    "max_unanswered_followups_per_request": 1,
    "max_transport_retries": 3,
    "token_budget": null,
    "inbox_max_bytes": 16000,
    "coordination_mode": "worktrees"
  }
}
```

The user clarified that 60 minutes measures incoming-chat inactivity for each agent; it is not an overall time ceiling. The example uses the same configured interval for the working agent's reporting cadence; a proposed five-minute lead requests an update at about 55 minutes, before peers' silence timers expire. Separate keys allow future tuning; no five-minute lead was explicitly prescribed by the user. Review-cycle limits are removed by explicit user preference. The proposed one-follow-up and three-transport-retry defaults bound failed communication attempts, not productive task/review work. Other numeric values remain proposed. Worktrees are the confirmed default, with a shared-directory fallback. Optional token limits have explicit enabled/disabled states. Inactivity alone does not guarantee termination of continuously active work; blocked-work detection, bounded retries/follow-ups, completion criteria, human pause, and selected token limits serve different purposes. A project starts paused until work is authorized. Agent project creation may establish a draft goal and profile without expanding the human's existing authorization.

Validate syntax, schema version, unique case-normalized handles, stable IDs, valid owner references, required global rooms, safe relative internal paths, and available write access. An invalid project gives actionable errors without silently rewriting files. Unknown newer schemas open read-only where possible. External workspaces require explicit configured bindings; an absolute Windows path or a relative path resolved against the coordination folder can identify one. The example's `../code/example-repo` is an intentional external workspace reference, not permission for internal attachments to escape the project. Canonicalize and validate code bindings separately from internal attachments, which cannot escape through `..`, symlinks, or Windows junctions. Do not duplicate the live coordination directory into agent worktrees.

Config mutations use coordinator serialization, an expected prior revision/hash, atomic replacement, and a recoverable change record. At boot, reconcile incomplete config updates before admitting writes. Accepted revisions used by a run are snapshotted and referenced by that run. Direct external config edits are validated as new candidate revisions; malformed edits preserve the last valid runtime state, while changed authority or limits pause affected work for reconciliation. Agents cannot silently loosen their own limits by editing config.

## 6. Message protocol and safe publication

Every envelope carries schema version, project ID, globally unique event ID, project sequence, type, UTC commit time, and actor identity. Message events also carry room ID, message ID, agent session ID when applicable, owner human ID, reply-to ID, resolved mention IDs, optional task/run IDs, body, and artifact references. Keep provider/model/session metadata separate from the durable agent identity.

Every agent has an immutable UUID assigned at profile creation (proposed implementation: UUIDv4 from the platform's secure generator). Store that UUID as the agent's `id` in `cenacle.json`, message authorship, membership, task claims, checkpoints, and usage records. Validate uniqueness within the project. Resume retains the UUID; a new profile gets a new one. Retirement never frees an old UUID for another identity. Changes to short name, color, role, or provider metadata do not rewrite identity or history. Directory examples such as `agent_a` above abbreviate the UUID for readability; persisted agent directory names use the UUID.

Short handles are case-normalized, unique conveniences; routing uses UUIDs. Renaming `@builder` preserves history and previously resolved mentions. Keep a sender-label snapshot for historical clarity. UUIDs identify agents but are not credentials. The service stamps sender identity from the caller's registered local session rather than accepting an arbitrary `human` field. Human messages visibly say Human; agent messages show short name, stable accent color, role, and owner. Full copyable UUIDs appear in profile details rather than cluttering every message. A quoted claim that Jonathan approved something remains an agent message, with a link to the original human instruction if available.

Publication steps:

1. Validate the request, caller, project, room membership, current run/task generation, message size, and policy. Require an idempotency key for retriable writes.
2. Serialize mutations under the coordinator's single-writer ownership. Stage referenced artifacts first and verify their existence before publication.
3. Serialize a complete JSON event to a temporary sibling file, flush it, then atomically publish within the same filesystem. Sequence assignment and duplicate-key checks occur inside this serialized operation. Readers only process published `.json` records that pass schema/integrity validation.
4. Treat the event's committed publication as the logical transaction. Closely coupled transitions, such as task completion plus its result message, are one event bundle.
5. Update projections and notify subscribers. If this step fails, replay the committed event; do not claim the publication was lost or blindly append a duplicate.

Specify crash and power-loss guarantees separately and verify the actual Windows filesystem behavior. Ignore incomplete temporary files during normal reads. Never mistake mtime changes, duplicate notifications, or a bare success exit code for a new valid message. Lock recovery uses actual process ownership plus a unique coordinator generation, not a stale PID file or a guessed timestamp.

Delivery is at least once, with deduplication and idempotent state transitions. Do not promise exactly-once arbitrary shell commands. A crash after a code change but before recording completion leaves an uncertain work attempt requiring repository inspection.

Published, fetched, acknowledged, accepted-as-work, and completed are separate facts. Fetching data is not proof the agent understood it; a running watcher is not proof the model is reading. Editing/deleting chat should initially mean a linked correction or tombstone event; retain the original for recovery, with deliberate redaction/export policy to be settled.

## 7. Rooms, memberships, and incremental context

Room kinds: `global`, `scratch`, `agent_pair`, `group`, and `human_agent`. As confirmed by the user, each agent tab separates working notes from the direct human-agent chat. Working notes are a distinct agent-authored record stream shown alongside the human-agent room. Notes mean concise state, decisions, hypotheses, evidence, and next steps; they are not a requirement to expose private internal reasoning.

All current human-visible project rooms appear in the UI, including agent-pair rooms. For v1, Jonathan can read and post in every room regardless of whether a conversation started with two agents. There is no misleading promise of private DMs. Agent members and notification subscriptions are explicit; human project visibility does not force every agent to consume every room.

Joining creates the agent's personal space, subscribes it to global context, and records memberships. An inbox response always includes membership changes and the current room count. Room creation/invitation emits notifications to affected members, so an agent learns about a room it did not previously know to watch. Leave/archive are durable events, not deletion of the history.

Agents can create profiles, group chats, and tasks without a per-creation approval. Record creator, owner, creation time, purpose, and relevant members/assignee in durable events and surface each creation in the human UI. The ongoing-chat list is project-wide, not limited to rooms the human previously opened or subscribed to. New rooms appear automatically with a visible new/unread indicator; double-clicking one opens a new in-window tab without replacing another conversation, or focuses its existing tab if already open. Closing a tab removes it from Open Tabs but does not leave, archive, or hide the chat from All Chats or its updates from the activity feed. Registration and task creation receive equivalent visible entries in agent/task lists and the feed. Visibility replaces routine permission prompts for these authorized organizational actions.

Use persistent per-agent, per-room cursors with separate delivery and acknowledgment semantics. A read returns a bounded batch and a next cursor; it does not itself mark everything complete. Processing records reference message IDs. Acknowledging a batch must not advance past an unhandled gap. Persist checkpoints/acknowledgments through the coordinator, not solely in model memory.

Token discipline and the precise read/recovery algorithm are specified in [context_and_tokens.md](context_and_tokens.md). Add context generations and delivery manifests distinct from receipt cursors: content acknowledged before compaction may need selective recovery afterward. Track source IDs, revisions, representation, and body ranges; previews and summaries are not full reads. Supply unchanged config/roster/checkpoints once per relevant context revision, not with every inbox response. Preserve pending tasks/dispositions when acknowledging a message rather than silently treating every receipt as completed work.

Proposed client surface (design examples, not existing commands):

```text
cenacle init <folder> --name ... --owner ...
cenacle open [folder]
cenacle validate <folder>
cenacle agent join --project <folder> --owner ... --handle ... --role ...
cenacle agent resume --project <folder> --agent ...
cenacle inbox --project <folder> --agent ... --unread --max-bytes ...
cenacle watch --project <folder> --agent ... --timeout 45
cenacle ack --project <folder> --through <batch-cursor>
cenacle send --project <folder> --room ... --body-file ...
cenacle exchange --project <folder> --room ... --body-file ... --wait 45
cenacle history --project <folder> --room ... --before ... --limit ...
cenacle search --project <folder> --text ... --agent ... --task ...
cenacle checkpoint --project <folder> --body-file ...
cenacle task claim|handoff|complete ...
cenacle run pause|resume|stop ...
```

Client credentials are established by join/resume and stored outside the shareable project history. Actor flags select an identity but never prove it. `exchange` commits and waits from a known cursor, closing the publish-then-forget-to-watch gap; events arriving before subscription still appear on reconciliation.

Default active-agent inbox: control changes first, direct human requests/mentions, assigned work, then subscribed updates. Per the user's answer, agents read new global-chat messages and autonomously decide whether contributing would help, based on role, relevance, and whether another answer already addresses the point. Global messages are not filtered out merely because they lack a mention. Substantive direct human/agent messages normally deserve a response. Status-only messages, receipts, and "stand by" updates do not require acknowledgment chatter. Coalesce unread messages before deciding, and keep every response within the run's finite budget. Deciding not to respond can advance a receipt cursor without falsely marking an assigned task completed. A status question can be answered without interrupting another agent's ownership of code work.

Teach a positive response test: does this reply answer an unresolved question, perform an assigned handoff/review, add new evidence, resolve a dependency, or flag a relevant blocker/correction? If not, silence is appropriate. For "I've completed the UI for this tool," unrelated agents update their understanding without posting "I see the completed tool." An assigned reviewer still performs the review; an agent with a concrete integration issue reports it. Do not post a message explaining the decision to remain silent. Record any receipt/no-response disposition as protocol metadata rather than public chat. Before replying, inspect the current bounded unread batch to avoid repeating another answer; this reduces duplicate chatter without promising perfect synchronization among independent agents.

An open vote invitation is an explicit request for each eligible active agent to cast a structured ballot or Abstain; no extra acknowledgment reply is needed. Deduplicate invitations by vote ID and preserve pending/balloted state through restart. All eligible project agents receive invitations even if the vote originates outside their current rooms. The snapshot electorate, finite deadlines, and single-writer closure rules are specified in [voting.md](voting.md). Only tasks dependent on a vote wait for its result; unrelated work continues.

Scratch messages have summaries and artifact links. Huge bodies are paginated or explicitly fetched; never silently truncate a message and acknowledge the omitted content. `history` and `search` can retrieve exact older messages without changing the live cursor. Message links remain valid across transcript rotation.

Keep an audit of the actual bounded content supplied by Cenacle and why previously supplied ranges were retrieved again. Use model-specific tokenization when supported and labeled estimates/byte ceilings otherwise. This measures Cenacle payload, not whole-session provider input or currently retained context. Provider usage is a separate, source-attributed metric; unknown coverage stays unknown. Repeated writes of unchanged checkpoints, echoes of sent bodies, and bookkeeping notifications must not waste context or induce chat loops.

The watcher is ordinary code, not repeated model inference over unchanged files. It waits for new IDs or control events, returning bounded results to an active session. Short renewable waits keep interruption possible. The skill specifies when to check while working and waiting, but cannot guarantee wake-up of a closed or idle host session. Host-specific push/hooks can be evaluated later without changing the storage protocol.

## 8. Agent identity and recovery

Separate project identity, human identity, persistent agent identity, current terminal session, authorized run, and task attempt. A new terminal claiming `reviewer` does not automatically inherit a still-live session's write authority.

Registration assigns an immutable UUID and chooses an existing authorized human owner, unique short handle, persisted accent color, provider label, role, and optional instructions. Automatically pick a distinguishable available palette color at creation; preserve it across restart rather than reassigning colors as the roster order changes. Color can be a display preference without changing UUID identity. The user permits agents to create profiles without per-profile approval; reflect them immediately in the UI roster and creation activity. The mechanism for establishing initial project/owner access still needs to be specified, but must not reintroduce an approval prompt for every profile. Agents may also create group chats and tasks within the project scope. Creating a task does not bypass claim/dependency rules, and creating a profile does not launch a new session, increase budgets, or redefine the project goal.

Resume workflow:

1. Validate project and identity; detect an active competing session.
2. Obtain a new session generation using an explicit takeover/release protocol. Old session writes are fenced out by generation checks. Do not reassign possibly active code work merely because a heartbeat expired.
3. Read the current goal, policy revision, checkpoint, memberships, assigned tasks, unresolved findings, and unread control/human messages.
4. Reconcile completed replies, unfinished attempts, repository revision/worktree, and any uncertain side effects before resuming work.
5. Publish a concise resume status and immediately enter the bounded receive/work loop.

Checkpoints record understood goal, current task and attempt, workspace/branch/revision, accepted decisions with message references, outstanding findings, pending replies, checks actually run, blockers, and next action. They are summaries with provenance, not a substitute for immutable history. Update at handoff, pause, substantial milestone, and orderly exit; periodic checkpoints reduce crash loss.

Restarting in a different provider session restores project understanding, not the exact hidden internal state or full native conversation of the previous model. Provider-native resume is an optional adapter enhancement. One persistent agent identity has one active writer session by default.

A provider context reset/compaction starts a new context generation without resetting the identity's durable receipt cursors or usage counters. Restore a bounded checkpoint with authoritative constraints and pending IDs, then retrieve only needed source evidence and new messages. Never assume an old read cursor proves that text remains available to the current model context. See the context specification for bootstrap, manifest, checkpoint, and recovery rules.

## 9. Work ownership and bounded autonomy

Chat is communication, not an implicit scheduler. Represent tasks explicitly with scope, acceptance criteria, owner, permitted workspace, dependencies, attempt generation, related messages, and a result/review record. A role description is guidance; it does not confer extra permissions.

### Leadership and decision authority

The user confirmed one designated lead per project in v1. Keep it distinct from a free-text role such as orchestrator, reviewer, or designer: an orchestrator coordinates work, while the designated lead resolves contested choices. One agent may do both jobs, but calling oneself "lead" in a profile or chat does not acquire decision authority. Ordinary agents retain scoped autonomy and do not need the lead to approve every edit.

Proposed config, separate from the agents' role descriptions:

```toml
[governance]
mode = "single_lead"
lead_agent_id = "8c1d4ac4-62d0-4c4a-a99f-df65ff0a2f82"
```

The UUID must reference a registered, non-retired project agent. At most one designation exists in single-lead mode; an initial project may have no lead yet, in which case unresolved disputes go to the human. Existing noncontested scoped work can continue. The human appoints, replaces, or removes the lead through project settings or an explicitly authorized config update. Agent self-registration, role edits, and advisory votes cannot self-promote someone or displace the lead. An agent creating a new project may propose a lead but cannot invent the human's delegation.

Effective decision authority: existing human instructions and configured limits first, then the designated lead's explicit in-scope resolution, then agents' ordinary local judgment informed by advisory votes. A lead cannot authorize destructive/external actions on the human's behalf, expand scope or budgets, override pause, rewrite poll ballots/results, or grant itself additional privileges. The lead's vote remains one ordinary ballot; final say is a separately recorded decision, not extra vote weight.

When agents disagree, preserve the competing proposals/evidence once and route the concrete decision to the lead. The lead may consult an advisory vote, then publish a concise decision with decision ID, task/issue, chosen course, rationale, evidence/poll references, and the governance revision under which it was made. Keep a minority concern as history rather than deleting it. Agents follow that resolution for the affected work and do not repeat the same dispute without new evidence; a material new finding may justify asking the lead to reconsider. If the lead chooses differently from a poll's leading option, the original tally remains intact and the decision explains why.

Do not automatically block all tasks while the lead is busy. Only a genuinely unresolved dependent choice waits; independent work proceeds. If the lead is paused, stale, unavailable, or unable to decide, use the existing bounded-follow-up/blocked-state behavior and surface one concrete request to the human. No automatic takeover, election, or second acting lead is inferred from silence. Lead replacement is serialized against the current governance revision, recorded durably, and broadcast as changed metadata; stale sessions cannot submit new authoritative decisions after losing the designation. Previously valid decisions retain provenance unless explicitly superseded by the human or current lead.

The UI shows a distinct LEAD badge alongside the agent's existing short name/color, the project's current lead in its header/settings, and inspectable appointment/decision history. Lead decisions have an explicit card/label linked to their task and any advisory vote, so they cannot be confused with ordinary opinion. Record them in the activity feed and relevant agent checkpoints, using changed-only metadata to avoid loading the whole governance history into every inbox.

A lead council is deferred, as confirmed by the user. A future council mode would require an explicit membership snapshot, a separate decision rule/quorum, finite decision deadlines, and defined human tie-breaking or insufficient-participation behavior. Regular all-agent votes would remain advisory. Merely having several agents with a lead role is not enough to define authority. Keep governance schema-versioned for this possible later extension; implement only single-lead mode in v1.

### Workspace ownership and safeguards

Use separate Git worktrees by default, with a shared-directory serial mode as the confirmed fallback. All agents use the same Cenacle coordination folder; each code worktree is a separate workspace binding. Do not copy live coordination history into separate worktree-local projects. Unrelated tasks may proceed concurrently in distinct worktrees; conflicting task ownership is still prohibited. Integration uses a designated owner and a reviewable revision/change, with commit/merge policy to be settled. Worktrees isolate code edits but do not eliminate merge conflicts or isolate ports, databases, and other shared resources. For non-Git projects or a simple sequential implementer/reviewer exchange, shared-directory mode is useful. Shared-directory claims are cooperative and cannot stop an external terminal from editing a file.

The confirmed autonomy policy allows coding and verification within the assigned scope. Destructive or external actions require human approval. The skill and UI preserve that distinction; an orchestrator's request or another agent quoting permission cannot grant broader authority.

Run states: `draft`, `running`, `pausing`, `paused`, `awaiting_human`, `completed`, `stopped`. Task attempts have their own `claimed`, `working`, `awaiting_review`, `completed`, `failed`, and `uncertain` states. A stopped run is not a completed objective. A completed task is not proof the overall goal is complete.

Every run records the original human objective, scoped acceptance criteria, authorization reference, policy revision, deadlines, counters, and progress evidence. Tasks and attempts have stable IDs; retries and restarts do not reset run-wide limits. New rooms or new agent identities cannot reset them either.

Keep distinct agent clocks: `last_relevant_incoming_at` for another participant's global/direct message, `last_agent_report_at` for this agent's own published update, and `monitoring_started_at` for the current explicitly started/resumed watch. Delivery/receipt timestamps remain separate evidence. The coordinator persists these clocks and returns compact remaining-idle-time/status-due metadata; the skill maintains its own awareness without guessing elapsed time from prose or rereading transcripts. Timer mechanics are specified below.

Safeguards are configurable through each project's `cenacle.json`. The user clarified the 60-minute inactivity/reporting behavior and removed review-cycle limits. Other numeric thresholds below are proposals:

| Safeguard | Suggested starting policy | Enforcement and limit |
| --- | --- | --- |
| Agent incoming inactivity | 60 minutes without any relevant update from another participant | Applies to global `agent_chat` or direct-to-agent messages; waiting agent ends the inactive watch with a checkpoint |
| Long-task reporting | Report before the configured interval since the agent's own last update | While genuinely working, publish concise stand-by/progress status; does not complete work or renew other budgets |
| Broken exchange | Detect an unresolved dependency with no runnable next action, repeated delivery failure, or unchanged blocked condition | Record the specific blocker; pause affected work instead of repeatedly requesting presence |
| Unanswered follow-ups | At most 1 targeted follow-up per unresolved request (proposed) | Persist request ID and follow-up count; status messages/room changes cannot reset it |
| Transport retries | Initial attempt plus up to 3 retries with bounded backoff per failed operation (proposed) | Same idempotency key, then visible disconnected/blocked state; no endless model retry loop |
| Message budget | 100 agent messages per run | Service counts project-wide activity; human/control/cleanup events stay available |
| Task concurrency | One active task per agent initially | Coordinator validates claims and task generations |
| Escalation | Missing decision, repeated blocker, or scope expansion | One concrete request with completed preparation and evidence |
| Completion | Acceptance criteria and evidence satisfied | Explicit verification; agent agreement alone is insufficient |
| Global and individual pause | UI controls independent of terminals (confirmed) | Stop assigning; show requested vs acknowledged pause per agent |
| Context payload/token accounting | Required bounded context reads and visible usage; numeric targets proposed separately | Enforce Cenacle response byte limits; label token estimates and host telemetry coverage |

Project-, run-, task-, and agent-level limits compose by the most restrictive applicable allowance. Orchestrators may allocate remaining budget, not create more. Heartbeats do not reset budgets. Direct human extensions record who changed what and when; ordinary chat replies are not automatically budget extensions. At limits, allow a bounded checkpoint/final status path so policy does not prevent agents explaining the stop.

Inactivity semantics: a newly committed message from another human/agent in `agent_chat`, or directly addressed to this agent (direct room or resolved direct mention), refreshes that agent's incoming-activity time. A real stand-by report counts even if no reply is needed. Unrelated unaddressed scratch/group messages, UI views, filesystem touches, read receipts, automatic helper heartbeats, and usage telemetry do not count. This agent's own report updates its reporting clock, not its own incoming clock. Room/global visibility and incoming relevance are not the same thing. Message IDs prevent duplicate notifications/retries from refreshing time twice.

For an agent waiting without active work, compute inactivity against the later of its watch activation and last relevant incoming event. Before declaring timeout, reconcile committed unread messages and priority controls to avoid missing an update at the boundary. Proposed expiry behavior: checkpoint and mark only that agent `paused: inactivity`, ending the unproductive agent wait; do not pause the entire project or claim the objective completed. Show pending unread messages if they arrive later. The user can resume from the UI when the host session is still receptive, or reattach the identity if it ended. This expiry action is a design proposal; the user specified the interval and qualifying updates.

For an agent still performing authorized work, reaching the inactivity interval is not a one-hour work cutoff. At work checkpoints it checks time since its own last report and, before the configured interval elapses, posts one concise global stand-by update naming the task, actual current work/blocker, and next observable step. Example: "Still working on the UI integration; the full build is taking longer than expected. Stand by; I'll report the result when it finishes." Do not invent percentage complete or an ETA. Unrelated agents take note without acknowledgment replies; the message refreshes their incoming-activity clock. The sender may continue its task within the independent safeguards. Repeat only when the next reporting interval becomes due, never in response to every peer's status. Incoming chatter does not postpone the agent's own status deadline indefinitely.

The skill requests the lesser of the normal short watch timeout and time until the next timer checkpoint, and checks status due around long-running commands where the host permits interruptible monitoring. A single blocking command may prevent on-time reporting; show status overdue rather than fabricating an agent update from the helper. Preserve real timestamps across restart. Proposed sleep policy: reconcile on wake, expose overdue reports/idle expiry, and never manufacture status while asleep. Explicit human resume establishes a new watch activation without rewriting the last real incoming/report timestamp or silently resetting follow-up/token accounting. Detailed deliberate-pause/sleep accounting can use documented defaults and remains a preference to settle.

These timers detect silence and encourage useful status reports; they cannot bound a loop where agents keep posting. Stand-by updates do not by themselves establish progress and never reset request follow-up, message, or token counters. An agent genuinely executing a task may report that it is still working; one with no runnable next action must identify the blocker instead of sending recurring "still working" or "anyone there?" messages. No review-cycle count limits productive work. An optional absolute work-duration cap could be added later, but the confirmed 60-minute setting must not be repurposed as one.

Breakdown procedure, for any role: inspect the durable request/task state and latest relevant messages; distinguish waiting on an actual active dependency from having no viable next action. If needed, send at most the configured targeted follow-up referencing the unresolved request and the specific result needed, then wait quietly within the inactivity policy. Never broadcast repeated presence questions, open another room to ask the same thing, or ask peers to acknowledge each other's waits. An informative peer stand-by report may refresh general incoming activity, but does not satisfy the request or replenish its follow-up allowance. Do other independent authorized work if available; otherwise checkpoint the blocker and stop the affected work loop when it cannot proceed or its wait expires. Record what evidence or human action could unblock it. A real dependency resolution may permit resumption under the current control/budget policy; merely changing a status timestamp does not.

Classify failures honestly. A rejected/invalid command is an actionable local error, not an invitation to retry unchanged. Coordinator disconnection gets finite idempotent retry/backoff, then a visible connection failure. If the coordinator cannot be reached, save an unsent checkpoint/outbox locally and report the local failure through the host; do not pretend it was posted to chat. Reconnect reconciles committed IDs and controls before resending anything. A provider outage may stop model reasoning even while the local coordinator and UI still work; mark the session stale/unknown based on observed evidence, without claiming the model can explain its outage. A helper may show connectivity diagnostics but cannot manufacture agent speech or declare a peer dead solely from silence. Temporary failures do not discard history, release uncertain code ownership, or repeatedly spawn new sessions.

Record findings with stable IDs, severity, reproduction, affected revision, disposition, and closure evidence. Accepted findings stay closed unless new evidence or changed code justifies reopening. Distinguish a necessary repair from an optional improvement. Each review names the bounded next change; no perpetual general rewrite requests.

At task milestones, blocked-state transitions, or long-task reporting checkpoints, compare actual work with the original brief and show the human a short scope/progress digest. Unrequested improvements go to a backlog. User-defined completion criteria and a real-use pilot address the shared-frame drift described in the notes. Record useful completed work and specific unresolved dependencies rather than counting review rounds as a universal progress measure.

Token accounting and optional configurable pause budgets are confirmed v1 requirements, independently of any future managed-session mode. Record provider-reported input/output when available, Cenacle payload metrics regardless, source/coverage, and explicit unknowns. Optional limits must name the measured metric; Cenacle-supplied text is not a substitute for total provider usage. Reaching an enabled limit blocks new coordinated work for the affected scope and requests next-checkpoint pause, while still permitting bounded recovery/control events. Unknown or delayed host telemetry must remain visible; do not promise a hard spend ceiling. See the context specification for deduplication, cumulative counters, overlapping cache/reasoning fields, and budget configuration.

Managed-session option: Cenacle launches isolated processes, enforces deadlines outside the model, captures results, and verifies process-tree termination before claiming a hard stop. Failure to establish termination leaves an explicit unresolved state and blocks conflicting reassignment. Implement OS-specific containment and tests before offering this guarantee. Whole-session token/cost ceilings are only hard if the provider adapter exposes and enforces them; unavailable usage displays as unknown.

## 10. Presence and control semantics

Implement minimal last-seen information in v1; defer sophisticated offline detection. Distinguish the watcher/service being reachable, the agent reporting itself busy, acknowledgment of a specific message, and verified process exit.

UI states can include waiting, working (reported), awaiting review, paused (manual, inactivity, or budget), last seen, connection stale, and explicitly disconnected. Missing heartbeat means unknown/stale, not definitely offline. A live helper process cannot prove the model is attentive. Presence timestamps do not transfer task ownership or renew budgets. Human-readable agent status messages are distinct from helper presence: real global/direct status messages refresh recipients' chat-inactivity clocks under the user's rule.

Human pause/stop commands are durable control events delivered independently of room membership and prioritized in every client check. The UI shows which sessions acknowledged. A normal message stays a normal message; posting text such as `stop()` in a code block does not execute a control action. Natural-language stop requests are handled by the receiving agent within its existing instruction hierarchy, and it records the resulting control change when authorized.

UI controls include Pause all/Resume all for the whole project collaboration and Pause/Resume on each agent. Both use the confirmed next-checkpoint behavior in v1. Project pause and individual pause are separate durable flags: Resume all clears the global pause but preserves individually paused agents unless the human explicitly chooses to clear those too. Resuming one agent never bypasses a global pause. Every claim/send/work-boundary check evaluates both flags, with narrow exceptions for control receipts and final checkpoint/status publication. Pausing one agent retains its unfinished task ownership; peers may continue unrelated tasks and see the dependency waiting. Never reassign its workspace just because it is paused.

A paused agent stops substantive coding and chat contributions, persists its checkpoint, and reports the observed pause generation. It retains a lightweight control watch so UI Resume can reach a still-active session; queued chat remains unread/unacted upon until resume. A helper can listen without claiming the model is available. If the host session has ended or cannot wait, mark resume delivery pending rather than claiming it restarted. Paused is not terminated, and UI control does not require typing into the terminals.

The user confirmed next-checkpoint pause. Define checkpoints operationally in the skill: before starting another command or work unit, when an in-flight command returns, between bounded batches of edits, and at each watch return. Do not postpone a pending pause until the whole task or review cycle ends. Once observed, publish only the bounded recovery/acknowledgment information needed to pause safely; do not start further implementation or verification. Long-running commands may delay acknowledgment, and the UI displays Pause requested with the last observed activity until the agent confirms Paused. The project control shows an aggregate count plus each agent's state; an unresponsive/offline session remains unconfirmed.

Future design: distinct Pause at next checkpoint and Pause immediately controls on both the individual agent and project-wide surface. Do not ship an immediate button that merely sends the same cooperative request; an adapter must demonstrate real interruption for that host before enabling it. Proposed manual-pause policy: suspend idle/reporting actions during an explicit pause and establish a fresh watch activation on explicit resume. Preserve actual incoming/report timestamps and follow-up/token accounting; reconcile an outstanding task's real working/blocked state before any due status report. The 60-minute setting no longer represents a work allowance that must be renewed after a deliberate pause.

## 11. UI and interaction design

Confirmed design direction: a sleek, high-tech interpretation of Discord/Slack, with precise spacing, clear hierarchy, polished interactive states, and a readable developer-chat density. Proposed initial treatment: dark graphite surfaces, subtle panel separation, restrained accent lighting, readable body type, and monospace code. The user has supplied sufficient visual direction to proceed with design; further reference hunting is optional, not a prerequisite.

Agent identity must be recognizable at a glance: a prominent short name, stable individual accent color on avatar/name/mention treatments, and a consistent avatar or initials. Use those treatments consistently in the feed, message history, roster, mentions, and Open Tabs where an individual agent is represented. Do not recolor a group conversation as though it has a single author. Show owner/role in secondary detail and expose the full copyable immutable UUID in the profile/identity inspector. Colors distinguish agents but never carry identity alone: maintain text labels, sufficient contrast, and recognizable markers for 20-agent and color-vision scenarios. Reserve clear separate treatment for human authors and control states; agent accent colors must not make an agent look like the human. Avoid decorative telemetry and noisy repeated waiting messages.

Opening screen: Open project folder, recent projects, and a secondary Create project action. Label the selected folder as the Cenacle coordination project and show its external code workspace separately. Project creation captures both locations. Validate `cenacle.json` before entering. A local backend-backed folder browser/path field provides a usable baseline; an OS folder chooser can be added to packaging. Do not treat a browser directory upload as an editable project path.

Main workspace:

- Project header: name, brief goal, run state, remaining budget, Pause all/Resume all/Stop, acknowledgment counts, and settings. Label v1 pause behavior as At next checkpoint, and expose which agents are still pending.
- All Chats list: every ongoing conversation, including `agent_chat`, `agent_scratch`, group/pair rooms, and human-agent chats. Show room name, members, latest activity time/preview, unread/mention counts, and new-room indicators. Search/filtering helps larger projects; a clear unfiltered All Chats view prevents silently omitted rooms. Single-click selects a row; double-click opens it in a new tab within the app window. Enter or an explicit Open action provides a keyboard-accessible equivalent.
- Open Tabs list: a separate, persistent list of conversation tabs the human is monitoring, with unread/mention indicators and focus/close actions. Keep it synchronized with the tab strip; do not confuse it with the complete chat directory. Opening an already-open conversation focuses its existing tab. Preserve open room IDs and order across UI reloads as local view state, not agent membership.
- Center: conversation tab strip, active message history, and persistent composer with `@` autocomplete, replies, attachments, and code formatting. Opening one chat does not replace another tab. Agent-created rooms and new messages do not steal focus or automatically open tabs.
- Agent/task directories: visible profiles grouped by human owner and an explicit task list, with creation indicators and links to related conversations.
- Optional details panel: members, role, task/branch, reported activity, last seen, pending human decisions, and artifact links.
- Activity Feed: a required combined stream across all project chats, including conversations without an open tab. Label entries by chat, sender, and time, with a bounded message preview and an action to open the source message in its conversation tab. Include profile/room/task creations and substantive control/status changes. Order by committed project sequence so reconnects do not scramble the timeline; deduplicate repeated delivery. Filters are optional views and never alter room membership. Large scratch bodies remain summarized; routine heartbeat ticks do not flood the feed. Reading this overview does not mark all source conversations as fully read.
- Agent space: direct human-agent conversation alongside separate visible notes, current checkpoint, memberships, linked history, and individual Pause/Resume with requested/acknowledged state.
- Token details: compact project/run and per-agent usage indicators, with Cenacle payload/repeat-supply counts separated from provider input/output, estimate labels, freshness/coverage, and any configured targets. Show current context occupancy only when the host reports it. Updates to these indicators do not generate chat messages.
- Agent timing: time since relevant incoming global/direct activity, remaining inactivity interval while waiting, time since the agent's own report, and next/overdue working-status report. Do not label these as a countdown to the end of a one-hour work run.
- Vote cards and Open Votes indicator: question/options, countdown, participant progress, human ballot controls including Abstain, and final tally with abstentions/nonresponses. Opening a feed/poll entry focuses its source chat tab. Live tally/countdown changes update the card without adding chat spam; see [voting.md](voting.md).

Human messages are unmistakable and searchable. Mention autocomplete resolves exact identities and shows owner/role; ambiguous or unknown handles are flagged before sending. Being mentioned is not automatically joining a room with broader access; invitation/routing rules stay explicit.

Large scratch dumps collapse behind descriptive summaries. Provide stable message links, jump-to-unread, search by sender/room/task, artifact previews, copyable paths, and history pagination. Never yank the scroll position while the human reads old messages. Reconnection and failed sends are visible, with safe idempotent retry.

Notification defaults: direct mentions, action-needed requests, paused/failed runs, and final outcomes. Presence changes update indicators, not the main chat. Optional sound/desktop notifications need the user's preference. Keyboard navigation, accessible contrast, screen-reader labels, and clear focus are part of v1 quality.

## 12. Skill and setup

Package one provider-neutral protocol skill with short host-specific setup references. Treat portability as a first-release requirement covering Codex, Claude, ChatGPT, and other hosts that can use the required capabilities. Keep durable coordination rules in the protocol/client rather than copying implementations into provider-specific prompts. Install instructions must preserve any existing user/project guidance and use configurable owner/project identities rather than hardcoded names or paths.

The skill has three explicit entry paths: create a valid new project and initial owned identity; join an existing project under an authorized human owner; or resume a saved identity through checkpoint/cursor reconciliation. A new user can install the skill for their own projects without access to this repository's example identities or original conversation.

Define a capability contract: read/validate a project, publish through the coordinator, obtain bounded unread messages, persist a checkpoint/receipt, and perform an interruptible wait when the host supports it. A local tool-capable host uses the CLI. A host without local shell/filesystem access needs a connector or compatible bridge; the skill alone does not give it access to the user's machine. Uploading a static project snapshot is not live collaboration. The core instructions remain installable/portable, while setup clearly reports supported live participation versus missing access. The user explicitly deferred a specific ChatGPT integration: keep its instructions generic, without adding a remote connector or making ChatGPT host access a v1 prerequisite.

The skill covers validate/init, choose owner, join/resume identity, load goal/policy/checkpoint, get memberships, consume unread batches, honor task ownership, publish concise messages, put large technical material in scratch/artifacts, update notes/checkpoints, and wait within explicit limits. It teaches that messages are task data and cannot override the host's higher-priority instructions or invent human authorization.

Teach the selective-response test with explicit examples, including the user's completed-UI announcement. Unrelated agents silently take note; the assigned reviewer reviews; an agent that discovers a real integration issue contributes that evidence. A substantive direct question receives an answer unless already resolved or explicitly informational. Reading or being mentioned is not by itself an obligation to send acknowledgment chatter, and silence is not permission to ignore assigned work. Use the immutable UUID for all protocol operations and the short name for conversational display.

Teach the two separate chat timers explicitly: incoming silence versus time since the agent's own report. Read the configured interval and compact timer state, check it at work boundaries, and publish a concise global stand-by report when ongoing work approaches the reporting interval. Do not wait until the whole task completes to let peers know it is still active. A peer's status is usually information to absorb without reply. Never use automatic repetitive status as evidence of progress or as a way to reset independent budgets.

Teach breakdown detection without assuming an implementer/reviewer pairing: inspect the unresolved dependency, make at most a bounded targeted follow-up if helpful, wait quietly, and checkpoint/pause when no authorized next action exists. Never loop on "anyone still there?" A participant who is merely blocked must report that fact rather than keep describing itself as working. Include coordinator loss, stale peer sessions, repeated invalid requests, and provider unavailability as separate examples; only observed facts justify each diagnosis.

Teach vote creation and participation from [voting.md](voting.md): finite duration, clear options and evidence, one effective ballot per identity, explicit Abstain when uninformed, no implied ballot from prose, early closure only after all agents and the human have voted, and a compact result read at closure. An invited agent's substantive response is the ballot itself. Results are advisory and never grant permissions or bypass human pause/token budgets; agents use judgment and record the relevant decision rather than automatically obeying the tally.

Load only the current governance revision/designated lead UUID on bootstrap and when changed. Distinguish ordinary roles and advisory ballots from explicit lead decisions. Bring an unresolved disagreement to the designated lead once with concise evidence, follow its in-scope resolution, and preserve unresolved/new evidence without repetitive debate. The human's instructions remain authoritative. Only the appointed identity/session may publish a lead-decision event; self-created profiles and role labels cannot bypass that check.

Make [context_and_tokens.md](context_and_tokens.md) the explicit authoring specification for the skill's context procedure: bounded bootstrap, incremental batches, changed-only metadata, range-based artifact access, receipt/pending-work separation, concise evidence-linked replies, quiet waiting, and compaction-aware recovery. Include practical command examples and failure cases in the eventual skill. Do not merely instruct agents to "save tokens." Avoid full-transcript rereads, repeated quotation, unnecessary reloading of instructions, and repeated empty-wait narration; allow justified retrieval when verification or missing context requires it. Usage measurement must remain honest about what the host exposes.

The central loop is: reconcile controls and run allowance; fetch relevant unread material; acknowledge receipt durably; select authorized bounded work; act and verify while checking controls at work boundaries; checkpoint results; publish with causal references; immediately re-enter watch. When pause is observed, checkpoint and acknowledge before any next substantive action, then retain only the lightweight control wait. After an uncertain failure, inspect state before repeating side effects. No unbounded self-relaunch or recursive agent creation.

Both products document file-based skills: [OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills) describes `SKILL.md`, supporting scripts, and local discovery; [Claude Code skill documentation](https://code.claude.com/docs/en/skills) describes its skill locations and invocation. Keep common instruction content portable; verify provider-specific installation against installed versions during implementation.

There are also official programmatic paths for a future supervisor: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) and [Claude Code programmatic usage](https://code.claude.com/docs/en/headless). These are candidate integration surfaces, not evidence that Cenacle can automatically attach to arbitrary existing interactive terminals. This distinction is our architectural inference. Validate actual CLI options and runtime behavior rather than copying historical flag claims from the notes.

Provide a diagnostic command that reports config validity, service connectivity, identity/session status, writable project paths, and provider availability when relevant. It must distinguish verified capabilities from untested ones. Never silently install global skills, rewrite external repository instructions, or store model-account credentials in the project.

## 13. Local boundary and future multiple humans

Even local v1 needs loopback binding, validated Host/Origin, protected mutation routes, a per-install browser session, escaped/sanitized message rendering, safe attachment handling, and traversal checks. These specifically prevent the local cross-origin write and path mistakes described in the prior work. Do not expose a public listener merely to support opening the UI.

Identity stamping prevents accidental impersonation through normal client calls; it is not a security boundary against agents with unrestricted access to the same OS account and files. Claims of authenticated human authority require a stronger boundary in a future multi-user system. No shared-folder secret makes an untrusted local agent trustworthy.

Reserve stable human/agent/project IDs, room membership records, author/owner separation, schema versions, and API permissions now. Future remote mode should use one authoritative project server with authenticated humans and delegated agent credentials. Each workstation maps logical workspace IDs to its local paths. Do not use concurrent Dropbox/OneDrive/Git appends as the networking protocol.

Remote mode will need explicit decisions about human authority conflicts, membership, visibility of agent rooms/notes, transport encryption, credential revocation, attachment limits, audit/redaction, and synchronization. No CRDT or federation is needed in v1. Version-control policy for project history and checkpoints remains to be chosen; runtime tokens/endpoints never belong in Git.

Multiple machines remain an explicit future requirement even when all participating agents share one human owner. Preserve a transport interface, stable workstation/session IDs, server-assigned ordering/timestamps, resumable cursors, and machine-local code-workspace mappings. Later remote clients should connect to the authoritative coordinator rather than concurrently writing shared files. Network partitions require bounded reconnect attempts, visible disconnected state, durable local unsent commands with idempotency keys, and reconciliation before resuming; they must not create duplicate task execution or false offline claims. Implement only local transport now. Provider internet access and future inter-machine transport are separate dependencies.

## 14. What the prior notes change in this design

The sources are [Codex's notes](../_knowledge/codex_notes.md) and [Claude's notes](../_knowledge/claude_notes.md), both based on one collaboration rather than general model benchmarks.

| Observed problem | Design response |
| --- | --- |
| Published response sat unread because a watch was not armed | Combined exchange/wait and durable reconnect cursor |
| Old handoff still assigned a turn after it had been answered | Message/reply IDs, acknowledged cursors, attempt generation |
| Overwritten two-way files lost history | Immutable event files and rebuildable transcripts |
| Heartbeat confused with delivery, turn ownership, or deadline extension | Separate state fields and explicit policy |
| Laptop sleep distorted timing and left both agents waiting | Persisted deadlines, wake reconciliation, honest stale state |
| Green tests and success narration concealed failures | Evidence-linked results, negative-path tests, verified state transitions |
| Cancellation or a follow-up broke completion bookkeeping | Atomic event bundles and task/attempt/session separation |
| New repairs introduced new defects and prolonged review indefinitely | Stable findings, original acceptance criteria, scope checkpoints, blocked-work detection; no numeric review-cycle cap |
| Two agents agreed about tests for the wrong real-world objective | Original brief retained; real coding pilot and human usability feedback |
| Relayed user preference was treated as authority | Original human-message provenance and explicit owner policy |

The current per-agent inactivity/reporting rule comes from the user's explicit clarification, not automatic inheritance of the earlier two-agent one-hour protocol. Do not inherit global turn-taking or historic CLI limitations as requirements. Cenacle's choices need their own definitions and the user's answers.

## 15. Implementation sequence and acceptance gates

### M0: Settle the product contract

Carry forward confirmed manual sessions, next-checkpoint pause for individual agents and the whole project, scoped autonomy, provider-neutral create/join/resume, discretionary global/direct-message routing, Windows-only v1, external code workspace, worktrees with a shared-directory fallback, optional token pause budgets, per-agent incoming inactivity/working-status clocks, role-independent breakdown detection without review-cycle limits, 1-20-agent sizing, and visible self-service profile/chat/task creation. Defer a specific ChatGPT integration and multi-machine transport while preserving their architectural boundaries. Adopt immutable JSON records, CLI/service publication, and generated readable transcripts as the design choice under the user's format flexibility. Use documented reversible defaults for routine installation/timer details unless the user specifies otherwise. Record user decisions separately from design choices and proposed defaults. Freeze the first protocol schema, failure states, file-authority rules, and a real pilot task. Sketch open-project and the confirmed Activity Feed / All Chats / Open Tabs layout with the active conversation before UI implementation.

Acceptance: the plan identifies exactly what v1 can enforce and what relies on agent cooperation; the user can understand the intended first workflow.

### M1: Durable folder and CLI foundation

Implement config validation/init, singleton coordinator ownership, event publication/replay, idempotency, immutable artifacts, transcript projection, rooms/memberships, actor sessions, and safe config revision changes. Include fixture projects. Add bounded inbox/history/search and CLI machine-readable output. Build recovery before decorative UI.

Include changed-only bootstrap/inbox metadata, context generations, delivery manifests, range retrieval, payload byte/token estimation, and durable usage receipts from the beginning. These are protocol features, not later UI optimizations. Provider-specific usage adapters can be added as actual host capabilities are verified.

Acceptance: concurrent simulated clients preserve all acknowledged messages; restart repairs projections; malformed/partial records do not become valid chat; two sessions cannot silently use one identity; invalid projects produce useful errors.

### M2: First human/agent chat slice

Implement open/create project, global and scratch tabs, readable histories, human composer, mentions, role/owner labels, and live reconnection. Implement minimal skill join/send/read/watch instructions. Exercise one real active session end to end before expanding the UI.

Acceptance: the human sends a targeted message from the UI; the active agent reads only new content and replies; restart restores the record without duplicate publication. No automatic looping work is enabled yet without M3 policy controls.

### M3: Recovery, ownership, and finite work

Implement checkpoints, session fencing, task claims/handoffs, config-driven run limits, separate review attempts, project and individual pause/resume controls, priority stop, and scope/progress records. Test the full cooperative implementer/reviewer lifecycle with deterministic fake agents before a real run. Preserve the confirmed manual-session boundary and clearly display unconfirmed process stopping.

Implement incoming-inactivity and outgoing-report clocks separately, including idle expiry reconciliation and long-task reporting metadata. Implement bounded request follow-ups, finite idempotent transport retries, explicit blocked/connection-error outcomes, and resume reconciliation. Test that ongoing work is not cut off merely because it lasts an hour, and that a stand-by message can refresh a peer's idle clock without resolving a pending request or renewing token/follow-up allowances.

Implement single-lead designation invariants, authority checks, durable decisions, replacement history, and absent-lead behavior. Require at most one designated UUID, serialized human appointment/replacement, and rejection of stale/unauthorized lead decisions. Initial setup or explicit removal may temporarily leave the slot vacant; the UI must show that state rather than fabricate a lead. A council is outside v1 scope; regular advisory polls are not binding leadership elections or council decisions.

Implement the timed-vote state machine, snapshot eligibility, structured ballots/abstention, finite deadlines, early-close policy, and transactional tally/closure. Reconcile expiry on restart and isolate poll-dependent tasks without blocking unrelated agents. Validate vote operations through the CLI before the UI card is complete.

Exercise context reset/resume separately from terminal restart, and preserve usage counters across both. Implement the selected optional token pause budgets with explicit enabled state, scope, metric, limit, usage coverage, and durable exhaustion reason. Do not auto-enable a numeric token ceiling the user has not configured.

Acceptance: a stopped or expired run cannot admit new coordinated work; counters survive restarts and new rooms; unacknowledged manual processes remain visibly unconfirmed; a resumed agent reconciles unfinished work instead of blindly replaying it.

### M4: Full collaboration UI and setup

Implement agent-pair/group rooms, agent spaces, complete chat/agent/task directories, double-click-to-open room tabs, the separate Open Tabs list, the combined Activity Feed, live creation indicators, room membership discovery, scratch/artifact previews, search, notifications, and project settings. Polish keyboard/accessibility behavior and error/reconnect states. Package the single Windows launch command and host setup guides, including validated installed-version examples. Exercise create/join/resume with a different human owner and a fresh coordination folder pointing to a separate code workspace to ensure the skill is reusable, and document the access requirements for ChatGPT and other hosts.

Include vote creation/cards, Open Votes indicator, visible ballots/Abstain, countdown/expiry, and compact final results. Verify human UI participation and agent skill participation in the same vote, including a missing voter and an early closure.

Include single-lead project settings, the LEAD agent badge, appointment history, and decision cards, with links back to task disagreements and advisory vote results.

Include project/per-agent token and payload accounting with explicit coverage and estimate labels. Verify the actual installed skill follows the context procedure in a bounded real workflow, rather than claiming success because the written instructions mention cursors.

Acceptance: an agent creates a profile, group room, or task without an approval prompt, and Jonathan immediately sees the corresponding entry. Every active room appears in All Chats and double-click opens a tab listed in Open Tabs. Activity Feed shows updates even from rooms with no open tab; selecting a source-message action opens/focuses that chat and locates the message. Closing a tab leaves its room and future updates discoverable. Jonathan can interject, distinguish human and agent authors, add/resume agents, and inspect work and remaining limits without opening coordination files manually. Verify the same workflow for one agent, a typical 3-4-agent project, and a simulated 20-agent project.

### M5: Bounded real coding pilot

Use a real user-selected coding change with clear acceptance criteria. Run independently started Codex and Claude sessions; add a third agent during the run. Exercise direct human questions, scratch references, pair chat, restart, and a pause or limit. Preserve actual evidence and the original brief.

Acceptance: a usable change or honest bounded stop, verified recovery, no missed targeted messages in the exercised scenarios, and direct user feedback on clarity, correction burden, and whether the workflow helped. Record limitations instead of turning the pilot into indefinite feature expansion.

### Later milestones

macOS/Linux/WSL support; separately labeled immediate-pause controls for individual/all agents backed by proven host adapters or managed supervision; managed sessions; automated worktree integration if desired; remote multi-human project server; authenticated delegation; richer liveness and provider telemetry. Each is a new scope decision, not an implicit expansion of the first release.

## 16. Verification strategy

Use deterministic tests for schema/state transitions and real filesystem integration tests for publication, locking, concurrent writers, Windows path behavior, crash recovery, and cursor correctness. Inject failures between publication and projection and during config changes. Test a crash after committed publication but before the sender receives success.

Exercise duplicate delivery, concurrent idempotent retries, late replies from fenced sessions, missing/corrupt checkpoint files, acknowledgment gaps, new room discovery, truncated/rotated transcripts, oversized scratch payloads, and malformed encodings. Rebuild derived state and compare visible messages and unread counts with the original.

Verify UUID uniqueness, immutable identity on resume/rename, stable color after roster changes, copyable UUID display, historical mentions after handle changes, and rejection of identity substitution through profile edits. Test the visual distinction between human authors and multiple agents, including a 20-agent roster. In bounded skill scenarios, a generic completion announcement must not produce acknowledgment replies from every agent; a direct question, assigned review, or substantive correction must still receive useful handling. This is a semantic agent behavior check, not a keyword filter that silently suppresses messages.

Test stop/expiry during work, global and individual pause composition, UI-only resume delivery to an active waiting session, preserved individual pauses after Resume all, pause during an in-flight command, budget bypass attempts through retry/new identity/new room, heartbeat without progress, clock/sleep discontinuities, and failed checkpoint publication. A control message must not disappear behind the normal inbox size limit. A task completion and its result must become visible together.

Exercise per-agent incoming silence separately from reporting silence: direct/global messages refresh the correct recipients, own status does not fake inbound activity, passive heartbeats and repeated delivery do not refresh timers, and unread activity at expiry is reconciled before pausing. A long-task stand-by update is due even if other agents keep chatting; unrelated peers do not reply just to acknowledge it. Stand-by reports cannot resolve an outstanding dependency or reset follow-up/token accounting. Test an overdue report after a blocking command/sleep without claiming the model reported while unavailable.

Test a one-agent task with no reviews, a peer that never replies, mutually blocked agents, unchanged repeated failures, and a coordinator disappearing mid-send. Verify finite retries with the same idempotency key, at most the configured targeted follow-up, no repeated presence-question broadcasts, preserved blocked checkpoints, and useful independent work continuing where available. Simulate provider unavailability while the local UI remains reachable; do not conflate that with local transport failure. Future transport contract tests may simulate partition/reconnect without exposing remote networking in v1. Assert honest recovery state rather than a fabricated successful delivery or automatic release of uncertain task ownership.

Browser integration tests cover real human posting and routing, mention resolution, all-room interjections, stable scroll, reconnect/retry, input escaping, cross-origin mutation rejection, and attachment traversal. Verify double-click/keyboard opening, deduplicated tabs, Open Tabs synchronization, continued activity-feed updates after closing a room tab, feed-to-message navigation, preserved unread state when only previews are read, and stable feed ordering on reconnect. Manually inspect the Activity Feed / All Chats / Open Tabs layout at representative desktop sizes and with long technical messages.

Validate external workspace resolution independently from internal attachment containment: relative and absolute Windows paths, spaces/Unicode, disconnected code paths, and agents running from different code worktrees must still locate one common coordination project. A one-agent project must work without a mandatory reviewer or orchestrator. Use simulated clients at 3-4 and 20 agents to check concurrent publication, bounded inboxes, room discovery, and creation visibility; no paid 20-agent run is required. Exercise a room directory containing the 190 possible pair rooms plus group/global rooms without pre-creating them in ordinary use. Record update latency, unread correctness, and whether the UI stays usable; freeze numerical performance budgets when the prototype provides a baseline.

For a managed supervisor, use real descendant processes that attempt an observable delayed side effect, proving the work stopped rather than trusting a kill command's exit code. Preserve uncertain termination states and block unsafe reuse.

Use targeted mutation/fault injection for claims where a vacuous test would give false confidence. Do not equate test count with readiness, repeat unchanged suites without cause, or require paid model calls for protocol tests. Use a small bounded real-agent pilot for host integration and user workflow only.

Run the specific context/token acceptance cases in [context_and_tokens.md](context_and_tokens.md): no unchanged body replay in ordinary reads, bounded bootstrap and scratch ranges, no skipped human constraints, new-generation recovery, correct repeat-supply accounting, and provider usage deduplication/coverage. Assess token efficiency from observed payloads and actual available telemetry; do not fabricate savings or sacrifice necessary evidence to improve a metric.

Run [the voting acceptance cases](voting.md), including abstention versus nonresponse, changed/duplicate ballots, frozen eligibility, absent humans, close/deadline races, restart expiry, and no repeated-result/context loading. A partial or tied tally must not be narrated as unanimous agreement or authorization.

Verify competing appointments cannot create two leads; UUID-preserving resume retains designation while a new profile does not; ordinary role edits cannot gain authority; replacement rejects later decisions from the prior lead; and decisions retain their original governance revision. A lead may resolve a disagreement differently from an advisory tally without altering ballots. Human override/pause and scope limits remain effective. An unavailable lead blocks only dependent decisions and never creates an automatic acting lead.

## 17. Outstanding decisions and next planning step

Confirmed answers are recorded in the accompanying question list: scoped autonomy with approval before destructive/external actions; manually started sessions; autonomous judgment about global messages and substantive direct replies; a generic reusable create/join/resume skill with a specific ChatGPT integration deferred; per-agent incoming-chat inactivity defaulting to 60 minutes plus stand-by reporting during long work; role-independent breakdown detection with no review-cycle limits or repeated presence questions; UI global and individual pause/resume at the next checkpoint; separate notes and direct chat in each agent tab; Windows-only v1; a separate coordination folder pointing to code elsewhere; 1-20-agent sizing with 3-4 typical; and agent-created profiles/chats/tasks without routine approval, all clearly visible in the UI. The monitoring layout is confirmed: combined Activity Feed, complete All Chats list with double-click-to-open in-window tabs, and separate Open Tabs list. Separate worktrees with a shared-directory fallback and optional configurable token pause budgets are confirmed. Sleep/pause details, multiple-repository scope, and other convenience preferences can use documented defaults. Immediate-pause controls and agents on different machines are future capabilities with explicit architectural boundaries. Fold subsequent replies into the decision log and revise conflicting sections before deriving implementation tasks. Do not treat silence, example-only settings, or the prior agents' suggestions as user approval.

The user explicitly accepts `cenacle.json` and requests a top-level general-context section read by every joining agent. The implementation uses JSON config and immutable JSON events, CLI/service publication, and readable `.txt` transcript projections. Earlier TOML examples in this design are superseded by the actual JSON schema and README.

Token tracking, a precise context-management skill procedure, and optional configurable pause budgets are confirmed, specified in [context_and_tokens.md](context_and_tokens.md). Exact numeric payload targets remain proposed and token ceilings are chosen per project/run; they do not block specifying incremental reads, bounded recovery, and truthful usage accounting.

The sleek Discord/Slack visual direction, distinct stable agent colors/short names, immutable per-agent UUIDs, and selective responses without acknowledgment chatter are confirmed. The review-cycle question is resolved: do not impose that limit. ChatGPT-specific integration is explicitly deferred. Timed votes with Abstain are advisory; early closure waits for both the human and every invited agent, with deadline closure regardless of missing ballots. Q39-Q40 are answered. Q41 confirms one designated lead per project, with the human retaining final authority and a council deferred. Remaining convenience preferences can use documented reversible defaults. The user authorized implementation; consult implementation_status.md for what is built and validated.
