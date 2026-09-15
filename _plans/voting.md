# Timed votes in chat

Status: planned first-release feature, requested by the user; no implementation yet. This extends [implementation_plan.md](implementation_plan.md). The user confirmed advisory results and early closure only after the human and every invited agent have submitted a ballot (Q39-Q40).

## Confirmed behavior

- An agent can pose a vote in chat, with a question, discrete options, and a specified open duration.
- Each invited agent should submit a ballot, and the human may vote while the vote is open.
- A vote waits for participants but closes at its deadline. It can close early when everyone required for early closure has voted.
- Abstain is an explicit choice, including when an agent lacks enough information to vote usefully.
- The human can see the vote, its state, and the result in the UI.
- Results are advisory: record the tally and let agents exercise judgment within their existing authority.
- Even if every agent has voted, keep the vote open until the human submits an option/Abstain or the deadline arrives. If everyone including the human submits a ballot earlier, close early.

## Proposed v1 semantics

Use a single-choice poll with at least two distinct options plus Abstain. Each eligible identity gets one current ballot. Equal ballot weights and visible ballots are the initial design choice; the human's existing project authority is not reduced by their numerical vote. No vote can approve destructive/external actions, change owner permissions, override an explicit human instruction, or raise budgets without the required human authority.

The user confirmed one designated lead per project (Q41), with a lead council deferred. Ordinary votes remain advisory and the lead casts one ballot like any other agent. If disagreement remains, the designated lead records an explicit in-scope decision referencing the poll; it may differ from the leading option without rewriting the tally. The human can override the decision. A tied advisory poll does not itself elect a lead or create a mandatory human tie-break; a possible future lead council would need its own decision rule. Appointment or replacement cannot be accomplished merely by an agent-created advisory vote.

Snapshot the electorate at creation: all registered, non-retired project agents, including the proposer, plus the current human. This follows the request for each agent to respond, rather than only the agents who happen to be online or in the source room. A paused, stale, or temporarily disconnected identity stays eligible until the deadline. New profiles do not join a live vote retroactively; retirement or lost presence does not silently shrink its electorate. Display the invitee list and pending count. This snapshot rule is a proposed default, not a host-liveness guarantee.

Votes may originate in any project chat. Store one canonical vote ID and a card in the source chat. Notify all eligible agents with a compact invitation, even if they have not opened that chat, and surface it in the human Activity Feed/Open Votes view. For a non-global source, include a compact reference in global chat so it is discoverable. Do not duplicate the full question or create separate polls. The invitation must contain enough shared context/evidence references to vote without silently joining every participant to unrelated chat history.

The creator supplies a positive duration; the coordinator stamps `opens_at` and `closes_at` using its clock. Display both an absolute deadline and a live countdown. There is no infinite-duration vote. The creation command/UI shows the deadline and frozen participation rules before publication. Proposed convenience default: a configurable project value may prefill the duration, but never invent an unstated deadline after opening. Choose a concrete numeric default during implementation rather than assuming the one-hour agent inactivity setting is the poll length.

Once open, freeze the question, option IDs/text, electorate, deadline, and tally/early-close rules. A material correction cancels/supersedes the vote with a linked replacement; do not change what existing ballots meant. Creator/human cancellation is an explicit recorded state with a reason. No silent duration extension or automatic reopening of tied/expired votes.

Abstain counts as a submitted ballot for participation and early closure, but as support for no option. A missing ballot is Pending while open and Did not vote after closure. Never turn silence, a paused agent, a failed send, or a generic chat acknowledgment into an abstention or a vote.

The confirmed early-closure policy requires every snapshotted agent and the human to submit a ballot (an option or Abstain). It does not mean a single option is mathematically ahead or that the first few voters agree. Close early even if the complete ballot set is split, and report that split honestly. If all agents have voted but the human has not, the vote remains open until the human votes or the deadline arrives. Likewise, a missing agent keeps it open until that ballot or the deadline. At the deadline, missing human or agent ballots do not prevent closure.

Deadline closure happens with whatever ballots were validly received. Show counts per option, abstentions, nonresponses, and total invited. Proposed tally presentation: identify a uniquely leading option among actual option ballots; label plurality accurately rather than claiming majority/consensus. A tie produces Tied; all abstentions or no option ballots produces No preference/result. Missing voters are not consent. No quorum requirement is needed to report an advisory tally, but low participation is explicit. Results do not automatically dispatch work or mandate the leading option. Agents may use their judgment and relevant evidence subject to an applicable human/lead decision; if choosing differently from the tally for the affected task, record a concise reason without reopening the whole debate. A tied or non-decisive result can be resolved by the lead when needed, with a concrete human escalation if the lead cannot resolve it or the choice requires human authority. Never automatically launch endless revotes.

Ballot changes are allowed while open, retaining revision history and counting only the latest accepted ballot for each identity. If the final required ballot closes the vote early, further changes are rejected; the UI explains that consequence. A ballot may include one brief rationale or evidence reference; Abstain may include a reason such as insufficient information. Long debate stays in chat/scratch rather than being copied into every ballot.

## Durable records and race handling

Use the existing coordinator/journal, not a separate authoritative voting database. Events include `vote_opened`, `vote_ballot_cast`, `vote_closed`, and `vote_cancelled`. A rebuilt `vibeguild_files/state/votes.json` can serve the UI; readable transcripts include the question, ballot/result references, and final tally.

Vote metadata includes vote/project/source-room IDs, creator identity/session, optional task/run reference, question, stable option IDs, electorate UUIDs/human IDs, timing, rules, revision, and status. Ballots include vote ID, voter identity, optional agent session generation, option ID or explicit Abstain, optional rationale, revision, commit time, and idempotency key. The server authenticates the voter using the existing session; a short name or UUID supplied as text is not proof of identity.

Serialize ballot acceptance and closure through the single writer. Recheck current vote state, eligibility, pause/authorization policy, and coordinator time inside the transaction. Reject ballots processed at or after `closes_at`; do not accept a stale client timestamp as evidence of timeliness. Commit the final required ballot and early-close result together in one event bundle. Deduplicate retry keys and enforce one effective ballot per voter. A reply saying "I choose A" in free text is not automatically parsed as a ballot; the agent calls the structured vote command and the human uses the card controls.

The coordinator schedules deadline closure without requiring any agent/model to keep polling it. On restart, reconcile overdue votes before accepting new ballots or dependent work. On reconnect, the UI renders an elapsed deadline as expired/pending reconciliation until it obtains the authoritative closed state; it does not leave voting enabled based on a stale countdown. Use resumable event IDs to deliver one logical result even if notifications repeat.

Pause does not disappear just because an agent was invited to vote. A paused agent does not perform substantive voting work until resumed, and an expired invitation is reported as missed. Proposed default: deadlines continue through individual/global pause and machine sleep; the UI makes this visible, and a human can cancel/reissue deliberately. This keeps votes finite without secretly granting unlimited extensions. Host inability to wake an agent remains visible as a missing ballot.

## Skill and context behavior

The skill teaches a specific voting workflow:

1. Pose a bounded, actionable question with distinct options, enough evidence, a duration, and an optional affected task. Do not manufacture a vote merely to avoid an available factual check or required human approval.
2. On an eligible open invitation, read the question/options/deadline and fetch only evidence needed to make an informed choice. An invitation is a substantive request even though ordinary status chatter can be ignored.
3. Cast exactly one effective ballot before expiry when the session is active and allowed to act. Use Abstain when information, expertise, or uncertainty prevents a useful preference. Do not invent confidence, copy another agent's rationale as one's own analysis, or require a prose reply after the structured ballot.
4. A ballot's acknowledgment is a short ID/status response, not a full reprint of the poll or all prior ballots. Duplicate invitations across global/direct/feed references resolve to the same vote ID and must not reload the full question.
5. Persist pending vote IDs/deadlines and own ballot disposition with recovery state. Resume fetches only changed open/closed state; it does not cast again because the terminal restarted. Changed question/options require a new vote, not invalidation of the prior ballot without notice.
6. Wait through the normal event watch. Only work depending on the result waits; independent authorized tasks continue. Do not repeatedly ask others to vote or acknowledge the tally. A finite deadline replaces a polling/repeated-reminder conversation.
7. On closure, read the compact result once and use it as advisory evidence for the affected task. Exercise judgment within the original authorization, recording the resulting decision and a concise reason when useful. Silence, abstentions, and ties never become unanimous approval, and the tally does not execute the leading option automatically.

Vote creation and an agent's actual ballot are authored contributions visible in the project; ordinary timer ticks and tally-projection refreshes are not new agent messages. They cannot generate an activity loop or repeatedly refresh inactivity clocks. Poll events obey the existing committed-event relevance rules; a human ballot is clearly human-authored. Voting counts toward actual token usage, and any enabled token budget/pause remains in force.

## UI

Render the vote as an embedded chat card consistent with the agent's short name/color and identity inspector. Include question, options, source/task link, proposer, deadline/countdown, participant progress, current ballot, and a clearly labeled Abstain control. Show who voted using names/colors with readable labels, not color alone. The full human UUID/agent UUID details remain inspectable through the existing identity UI.

Use a compact Open Votes view/indicator for active polls across all chats, plus creation/closure entries in the Activity Feed. Opening the card focuses the source chat tab and message. Keep the composer distinct from ballot controls so typed discussion cannot accidentally cast a vote. Live updates modify the card rather than adding a separate system message on each countdown tick. Optional ballot rationale expands on demand.

Closed cards show the immutable final tally, abstentions, nonresponses, whether closure was early/deadline/cancelled, and whether the result is advisory. Disable submission on closure with a clear result when a concurrent send loses the deadline race. Inform the human when early closure is enabled and whether their ballot is required for it.

## Acceptance checks

- One agent plus a human can open, vote, abstain, and close a poll; a simulated 20-agent electorate behaves the same without flooding chat.
- Every eligible agent receives one logical invitation, including agents outside the source room. New/retired profiles and presence changes do not rewrite the frozen electorate.
- Abstain satisfies participation; missing votes remain nonresponses. Ties and all-abstain/no-ballot cases are explicit.
- All agent ballots with an absent human leave the poll open until the human's option/Abstain or deadline; the reverse missing-agent case also waits. A leading option does not close early before all required ballots arrive.
- Ballot edits, duplicate retries, fenced sessions, ineligible identities, simultaneous final ballots, cancellation, and exact-deadline races produce one consistent tally and closure.
- Service restart/sleep/reconnect reconciles expiry; a paused or closed host is never reported as having cast a ballot.
- The human votes from the UI, sees updates/results in the feed and chat tab, and can distinguish discussion from an actual ballot.
- The skill casts or explicitly abstains on an actionable vote, skips redundant acknowledgment messages, preserves pending/balloted state on resume, and avoids reloading unchanged poll context.
- A vote never overrides human authorization, budget/pause controls, or produces automatic repeated votes when no decision is reached.
