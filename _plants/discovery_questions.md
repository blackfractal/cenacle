# Cenacle discovery questions

Status: initial answers recorded; 2026-09-13. These questions refine [implementation_plan.md](implementation_plan.md). Answer open questions in any order or by ID. Defaults are recommendations, not decisions. Not every preference must be settled before starting implementation; the architecture questions should be settled first.

## Current priority questions

Q41 is answered: one designated lead per project, with the human retaining final authority and a council deferred. Earlier main questions, including timed-vote Q39-Q40, are also resolved. Votes are advisory and stay open for the human until their ballot or deadline, even after all agents vote. Q08 defines per-agent inactivity/status reporting and removes review-cycle limits. Q37 defers a specific ChatGPT integration; Q04's worktree default and Q38's optional token pause budgets are confirmed. The rest is a reference backlog of preferences, not a requirement to answer every question before implementation. Use documented reversible defaults for routine choices; preserve all confirmed answers.

## First decisions: autonomy and work

1. **Q01 — Agent authority — ANSWERED:** Work autonomously within a scoped task; ask before destructive or external actions. Specific treatment of local installs/commits/merges can be clarified in setup; existing host permissions still apply.
2. **Q02 — Session management — ANSWERED:** V1 coordinates sessions the human starts independently. No launching/supervision in v1.
3. **Q03 — Stop guarantee — ANSWERED:** Next-checkpoint pause is acceptable for v1, for individual agents and the whole project. Immediate pause may be added later as a separate control backed by actual host interruption; do not require process supervision for v1.
4. **Q04 — Workspace ownership — ANSWERED:** Separate Git worktrees by default, with a shared-directory fallback for sequential work. All worktrees point to one common Cenacle coordination folder. Integration still needs ownership and shared services need coordination.
5. **Q05 — Coordination style — RESOLVED THROUGH Q41:** One designated lead has final say in agent disagreements within scope; the human retains final authority. A council is deferred. Distinguish the lead's decision authority from an optional orchestrator's scheduling role; one agent may perform both.
6. **Q06 — Response routing — ANSWERED:** Agents autonomously decide whether to respond to global `agent_chat`. Direct messages from the human or another agent normally deserve a response unless there is no useful reply, such as "I'm writing up what you requested, stand by." The user reinforced that a completion announcement such as "I've completed the UI for this tool" should not elicit "I see the completed tool" from every agent. Teach useful contribution rather than acknowledgment chatter; assigned review and substantive questions remain actionable. Do not impose mention-only global routing.
7. **Q07 — What counts as done:** Should you define acceptance criteria before each run, can an agent draft them for you, and who can declare the project complete? Proposed default: agent drafts allowed, human objective retained, results linked to verification.

## Safety and loop limits

8. **Q08 — Inactivity/reporting — ANSWERED:** Each agent has a configurable incoming-chat inactivity timer, default 60 minutes without updates from anyone else directly to that agent or in global `agent_chat`. An agent still working near an hour since its own last report should post a global stand-by update explaining it is still working. This replaces the earlier one-hour run-cap interpretation and 15-minute idle proposal. Track incoming activity and own reporting separately. The user explicitly removed review-cycle limits: some agents do not receive reviews. Detect broken/stalled collaboration and stop unproductive presence-question loops instead; bounded follow-up/retry numbers in the plan are proposed implementation defaults.
9. **Q09 — Exhaustion:** At a limit, should all agents pause, only the affected task pause, or should the orchestrator finish within the existing remaining budget? Proposed default: pause the affected scope; always preserve a checkpoint/status path.
10. **Q10 — Renewal:** May an orchestrator redistribute a fixed budget? Should only you extend the total? Proposed default: only the human extends totals; agents cannot reset counters by restarting.
11. **Q11 — Sleep and unattended work:** Will this run overnight/on a sleeping laptop? Proposed default: retain actual incoming/report timestamps and reconcile idle expiry or overdue reports on wake; do not fabricate status during sleep. The 60-minute setting is an inactivity interval, not a work-duration budget.
12. **Q12 — Human interruption — ANSWERED; TIMER DETAIL PROPOSED:** UI controls pause/unpause individual agents and the entire project independently of terminals, at the next checkpoint for v1. Show requested versus acknowledged pause. The user may want separate convenient/immediate controls later, for both scopes. Proposed timer behavior: suppress inactivity/report actions during explicit pause, establish a fresh watch activation on human resume, and preserve actual message timestamps plus follow-up/token accounting.
13. **Q13 — Disagreements and blocked work — REFINED BY Q41:** No numerical review-cycle cutoff. If a disagreement blocks the task, preserve the concrete issue/evidence and ask the designated lead for a decision. Escalate once to the human if the lead is unavailable, cannot resolve it, or human authority is required. Continue independent work where possible.
14. **Q14 — Scope drift:** How often should you receive a brief comparing current work to the original goal? Proposed default: at meaningful milestones and review/time limits, without repeated waiting chatter.

## Files, installation, and project organization

15. **Q15 — Platforms — ANSWERED:** Windows only initially. Keep future macOS, Linux, and WSL support in mind, with platform-specific code isolated from the protocol.
16. **Q16 — Installation:** Is a Python command acceptable? Would you prefer an npm command, a packaged executable, or another installation style? Proposed default: one launch command serving a browser UI.
17. **Q17 — Project location — PARTLY ANSWERED:** The Cenacle coordination folder is separate and points to code somewhere else. No repo-local default. Still open: whether one project needs to cover multiple code repositories in v1; start with an explicit external workspace binding.
18. **Q18 — File contract — ANSWERED / DESIGN CHOSEN:** The user leaves this open to the most appropriate pattern; files may be structured JSON and need not be free-flow text. Design choice: immutable JSON event files, publication through the CLI/service, and generated readable `.txt` transcripts. This simplifies parsing/identity/cursors and isolates atomic publication per event. The number of small files is a tradeoff to measure. The user permits the format choice but did not specifically prescribe this exact layout.
19. **Q19 — Config style:** Is TOML inside `cenacle.json` comfortable, or do you prefer YAML, JSON, or another format? Proposed default: roster and short roles in the top-level file, longer role instructions in separate Markdown files.
20. **Q20 — Git and retention:** Should chat/history/notes be committed with code, live outside Git, or be selectively exported? Should original messages ever be deleted, and how should secret redaction work? Proposed default: runtime/cache excluded; transcript retention chosen explicitly.
21. **Q21 — First scale — PARTLY ANSWERED:** Minimum 1 agent, typical 3-4, and about 20 as the initial upper sizing target, with room to grow. Do not hardcode 20 as a lifetime identity limit. Room count, simultaneous projects, and typical scratch sizes are still open; directories must scale beyond a handful of chats.

## Identity and permissions within a project

22. **Q22 — Joining — PARTLY ANSWERED:** Agents may create profiles without asking each time, provided they are clearly visible in the UI. Still define how a terminal establishes initial project/owner access, without turning that into repeated per-profile confirmation.
23. **Q23 — Agent initiative — PARTLY ANSWERED:** Agents may create profiles, group chats, and tasks without asking. Each creation must be clearly visible in the UI. Creating profiles does not launch sessions; v1 still uses manually started sessions. Role changes/invitation policy can be specified separately; task creation remains within the existing goal and ownership rules.
24. **Q24 — Resume and takeover:** If two terminals claim the same agent identity, should the second be rejected, ask you to take over, or be assigned a new identity? Proposed default: reject silent takeover and offer explicit recovery.
25. **Q25 — Identity continuity:** Can a saved identity change from Claude to Codex while retaining its name/history, or should provider changes create a new identity? Proposed default: identity can persist, with provider/session changes recorded visibly.
26. **Q26 — Ownership later:** For future multiple humans, should each human control only their agents, or can a project owner pause everyone's agents and inspect every room? This need not be implemented now, but affects future authorization design.

## UI and everyday interaction

27. **Q27 — All chats at once — ANSWERED:** One combined activity feed showing which chats are updating; a complete All Chats list where double-click opens a conversation in a new tab in the app window; and a separate list of currently Open Tabs for conversations the human is monitoring. New rooms appear automatically in All Chats. Closing a tab does not remove the room or its updates from the feed. No tiled view is needed in the initial plan.
28. **Q28 — Agent personal space — ANSWERED:** Yes: separate visible notes and direct chat within the agent's tab. Notes cover working state, decisions, and blockers.
29. **Q29 — Direct-room visibility:** Should every room always be visible and writable by you, including agent-to-agent rooms? The brief says yes; confirm any exceptions. Proposed default: no private rooms in v1.
30. **Q30 — Messages:** Which matter immediately: reply threads, message edits, reactions, pins, attachments, images, code highlighting, search, or read receipts? Proposed default: replies, code, text artifacts, search, and honest receipt states; richer chat features later.
31. **Q31 — Visual direction — ANSWERED:** A sleek high-tech version of Discord/Slack. Agents are easily identified by distinct stable colors and short names, with an immutable UUID for every agent in the project. Proposed treatment: dark graphite surfaces, restrained accents, readable chat density, and clear Human/Agent distinction; a light theme can be considered later. No additional visual reference is required before design work.
32. **Q32 — Notifications:** In-app only, sound, desktop notifications, or a taskbar/tray indicator? Which events should interrupt you? Proposed default: mentions, decisions needed, stops/failures, and completion.
33. **Q33 — Project creation:** Should the app offer a full project wizard? When an agent creates a project, can it draft the goal and add itself immediately? Proposed default: yes, with a paused draft until work is authorized.

## Pilot and priorities

34. **Q34 — First real task:** What actual coding change should the first implementer/reviewer pair complete? Who implements, who reviews, and what result would make you say Cenacle helped?
35. **Q35 — First milestone priority:** Is your first priority reliable CLI/skill collaboration, a polished human UI, or a small end-to-end slice with both? Proposed default: a thin complete chat slice followed by recovery/safety before autonomous work.
36. **Q36 — Unacceptable failure:** Which is worst for you: missed messages, duplicate coding work, agents spending too long, too many permission questions, or hard-to-follow chatter? Rank them or name another; this shapes the pilot checks.
37. **Q37 — ChatGPT access — ANSWERED:** Keep the skill generic; defer a specific ChatGPT integration. No ChatGPT connector/host implementation is required in v1. Portable instructions still document the capability contract for any participating host.
38. **Q38 — Tokens and context — ANSWERED:** Track usage and allow optional configurable pause budgets. Token count is important, and the skill must teach precise context management to avoid unnecessary rereading. The procedure is in [context_and_tokens.md](context_and_tokens.md). Numeric thresholds are selected through configuration, not imposed universally. Keep provider usage separate from Cenacle payload counts/estimates and explicitly show unknown coverage.

## Timed votes

39. **Q39 — Vote authority — ANSWERED:** Advisory: record the result and let agents use judgment. No automatic execution of a winning option or expansion of authority. The core requested feature—agent-created votes, human participation, finite duration, early closure, and Abstain—is confirmed; see [voting.md](voting.md).
40. **Q40 — Human participation and early closure — ANSWERED:** Keep the vote open for the human until they vote or the deadline arrives, even if every agent has voted. Early closure requires all invited agents and the human to have submitted an option or Abstain. A missing ballot does not count as abstention; at the deadline, close and report nonresponses.

## Leadership

41. **Q41 — Lead designation — ANSWERED:** One designated lead per project; consider a lead council later. The human retains final authority. The plan includes UUID-based designation, at most one lead, explicit in-scope decisions, a visible LEAD badge, and absent-lead/replacement behavior. Advisory polls remain separate from the lead's final say.

## Decision log

| Decision | Source/date | Plan impact |
| --- | --- | --- |
| Generic reusable skill for Claude, Codex, ChatGPT, and other capable hosts; create, join, and resume workflows | Direct user follow-up, 2026-09-13 | Sections 1, 2, 12, M0, M4; host capabilities and access are explicit |
| Scoped autonomy; ask before destructive/external actions | Q01 response, 2026-09-13 | Requirements, ownership/authority rules, M0 |
| Coordinate sessions the user starts; no session management in v1 | Q02 response, 2026-09-13 | Scope, release boundary, M0/M3; managed supervision stays future work |
| Agents judge global-message relevance; normally answer substantive DMs; skip empty acknowledgments | Q06 response, 2026-09-13 | Requirements and inbox/routing behavior |
| Settings live in `cenacle.json`; 60 minutes is per-agent incoming inactivity, with a stand-by report near the interval when still working; no review-cycle limit | Q08 initial response and later explicit clarifications, 2026-09-13 | Supersedes prior three-cycle default and run-duration/15-minute-idle proposals; separate incoming/report clocks and role-independent blocked-work behavior |
| UI pauses/resumes all agents and individual agents independently of terminals, at the next checkpoint for v1 | Q08 follow-up and explicit pause answer, 2026-09-13 | Requirements, control state composition, work-boundary checks, requested/acknowledged UI, M3, verification; immediate pause is future work |
| Separate notes and direct human-agent chat within each agent tab | Q28 response, 2026-09-13 | Requirements, room model, agent-space UI |
| Windows only for v1; preserve a path toward macOS/Linux/WSL | Setup response / Q15, 2026-09-13 | Requirements, scope, platform interfaces, setup and later milestones |
| Coordination project folder points to code elsewhere | Setup response / Q17, 2026-09-13 | Requirements, external workspace binding, example config, opening/setup, verification |
| 1 agent minimum, 3-4 typical, about 20 initially; allow growth | Setup response / Q21, 2026-09-13 | Requirements, subscriptions/pagination, room-list sizing, simulated load checks |
| Agents create profiles, group chats, and tasks without asking; all must be very visible | Setup response / Q22-Q23, 2026-09-13 | Registration, creation events, complete chat/agent/task directories, M4 acceptance |
| Combined Activity Feed, complete All Chats list with double-click-to-open in-window tabs, and separate Open Tabs list | Setup response and explicit Q27 answer, 2026-09-13 | Required UI navigation/feed, new-room indicators, tab lifecycle, M4 acceptance and browser verification |
| Structured text/JSON is acceptable; choose the most appropriate storage pattern | Q18 response, 2026-09-13 | Design selects immutable JSON events, CLI/service publication, and generated `.txt` transcripts; exact schema follows in M0 |
| Token tracking is important; the skill must teach precise context management to minimize unnecessary rereads | Direct user instruction / Q38, 2026-09-13 | New context/token specification; protocol manifests/generations, bootstrap and delta rules, bounded artifacts, UI metrics, M1-M4, verification |
| Sleek high-tech Discord/Slack UI; agents identified by distinct colors, short names, and immutable per-project UUIDs | Direct user follow-up / Q31, 2026-09-13 | Requirements, UUID config examples and identity rules, stable color allocation, UI treatment, identity/visual verification |
| Completion announcements do not require every agent to acknowledge; teach selective useful replies | Direct user reinforcement / Q06, 2026-09-13 | Explicit response test and examples in routing, skill specification, context procedure, and verification |
| Worktrees by default, shared-directory fallback | Explicit Q04 answer, 2026-09-13 | Requirements, config default, workspace ownership, M0 and outstanding decisions |
| Track token usage with optional configurable pause budgets | Explicit Q38 answer, 2026-09-13 | Requirements, budget metrics/coverage and exhaustion behavior, context specification, M3 |
| Keep the skill generic and defer a specific ChatGPT integration | Explicit Q37 answer, 2026-09-13 | Capability contract and M0; no ChatGPT-specific v1 dependency |
| Recognize broken collaboration; stop repeated "anyone still there?" messages; same-machine v1 with future multi-machine agents | Direct follow-up rejecting review-cycle limits, 2026-09-13 | Bounded targeted follow-ups, finite transport retries, blocked checkpoints, honest local/provider failure states, future remote transport boundaries, verification |
| Agents pose timed advisory chat votes with explicit Abstain; early closure requires every invited agent and the human to vote, otherwise wait until deadline | Direct voting request and explicit Q39-Q40 answers, 2026-09-13 | Voting specification, durable ballot/closure state, advisory task decisions, UI cards, human participation window, skill, M3/M4, context handling, verification |
| One designated lead per project settles agent disagreements within scope; human retains final authority; council deferred | Direct leadership proposal and explicit Q41 answer, 2026-09-13 | Confirmed single-lead designation, authority/appointment/decision rules, UI badge/settings, absent-lead behavior and verification; polls remain advisory |

Unanswered proposed defaults remain open. Retain question IDs when recording subsequent decisions and revise the plan sections they affect.
