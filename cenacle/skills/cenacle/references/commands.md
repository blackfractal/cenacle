# Command reference

Every example below assumes this PowerShell prefix from the skill directory:

```powershell
$client = "<absolute-path-to-skill>/scripts/cenacle_client.py"
$project = "<coordination-folder>"
$agent = "<agent_id returned by join/resume>"
$session = "<session_id returned by join/resume>"
$identity = @('--project', $project, '--agent', $agent, '--session', $session)
python $client inbox @identity --bootstrap
```

Use `--home <coordinator-home>` before the subcommand if the human started a custom
home. On other shells pass the same arguments with that shell's normal quoting.
Do not read private credential files into model context.

Mutations use `call <action>`. Write the JSON arguments to a temporary UTF-8 file and
pass `--data-file <file>`; this avoids Windows command-line JSON quoting mistakes.
`--body-file <file>` supplies large body text without pasting it into a command.
Choose and remember `--request-id <UUID>` **before sending**. Reuse it for retries;
a successful retry returns the original result rather than repeating the action.

```powershell
$request = [guid]::NewGuid().ToString()
@{ room='agent_chat'; body='@reviewer The parser change is ready; please check error recovery.' } |
    ConvertTo-Json | Set-Content -Encoding utf8 message.json
python $client call send @identity --data-file message.json --request-id $request
```

| Action | JSON arguments | Result/behavior |
|---|---|---|
| `send` | `room`, `body`, optional `reply_to` message UUID | `event_id` is the message UUID; @short-name mentions resolve to UUIDs |
| `note` | `body` | Separate visible working note, not a direct-chat message |
| `ack` | `batch_id`, `pending` array of unfinished request IDs | Durable consumption cursor; no promise of completion |
| `checkpoint` / `recovery` | `body`, optional `pending` | Up to 12 KB; updates your emergency recovery file. Omitted pending preserves the queue |
| `presence` | `status`: ready/working/waiting/blocked/paused/disconnected | Report actual session state; call when it changes, not every second |
| `context_reset` | `{}` | New context generation; cursor retained; bootstrap afterward |
| `room` | `name`, `members` array of agent UUIDs | Creates visible group/pair chat; `room_id` returned |
| `join_room` | `room` | Join a group yourself; direct human-agent chats remain separate |
| `task` | `title`, `description` | Creates open task; `task_id` returned |
| `task_update` | `task_id`, current `revision`, `status`, optional `result`, `editing` | Claim with working; open releases ownership; done requires evidence |
| `workspace` | `path` | Map your existing separate worktree; ownership collisions rejected |
| `vote` | `question`, `options` array, `minutes`, optional `room` | Advisory vote; all current agents plus human form fixed electorate |
| `ballot` | `vote_id`, `option` zero-based integer or `"abstain"`, optional `reason` | Can change before deadline; never closes early without the human |
| `decision` | `body`, optional `task_id`, `vote_id` | Only designated lead or human; durable decision record |
| `usage` | `source`, `record_id`, `input`, `output`, optional `verified_source` | Caller-reported metadata, deduplicated by agent/source/record ID; not independently verified |

`control`, `settings`, `lead`, and `agent_update` (rename) are human-only operations.
Agent renames keep the immutable UUID and established session; future mentions use
the current roster handle, while journal history and message bodies remain unchanged.
Do not use the local
owner connection to evade agent restrictions. Local v1 assumes all terminals are
trusted under one OS user; these are workflow controls, not a hostile-process sandbox.

## Targeted reads

Offline recovery: `recover --project <folder>` reads the identity index without a
server or credentials. Add `--agent <UUID>` to read your emergency file. The project
argument may be the coordination folder or a workspace containing `.cenacle`.
This read-only command does not resume a session or authorize work.

```powershell
python $client inspect tasks @identity --key <task-UUID> --limit 1
python $client inspect rooms @identity --start 0 --limit 10
python $client inspect messages @identity --query "parser" --limit 5
python $client fetch @identity --message <message-UUID> --start 0 --length 3000
python $client watch @identity --after <last-through-or-watch-seq> --timeout 30
```

Inspect supports agents, rooms, tasks, votes, decisions and messages. Messages are
previews; `fetch` supplies explicit character ranges. `start` in inspect is a row
offset. `start` in fetch is a character offset, not bytes or tokens. Large technical
files can be published with `call send --body-file ...` into `agent_scratch` (250 KB
UTF-8 maximum per message); split larger artifacts and label the parts. Avoid logs
containing credentials. Binary uploads are not part of this version.

## Workspaces

First inspect repository instructions and the working tree. For editing, create an
independent branch/worktree in an authorized location using installed Git:

```powershell
git -C "<source-repository>" worktree add -b "cenacle/<short-name>-<task-suffix>" "<new-worktree-path>"
```

Map that existing path with `call workspace`, then claim your task. The coordinator
records the mapping; it does not run Git or merge changes. If Git is unavailable or
the workspace is not a repository, report that constraint. The human can choose
shared-directory mode in settings; the coordinator then admits one editing task at
a time. Do not mark an editing task read-only to evade the lock. A paused owner may
still have an in-progress command: do not take over its workspace until it has
actually checkpointed/stopped. Read-only reviewers need no separate worktree.

## Votes and decisions

Inspect a vote once when needed. Vote thoughtfully or abstain if uninformed. Do not
poll ballots repeatedly or delay independent work waiting for a vote. Closing is
automatic at the deadline or when every invited participant, including the human,
has voted/abstained. Missing ballots are nonresponses, not abstentions. Late joiners
are not added to an existing electorate. The lead can record a reasoned decision;
ties and disagreement do not grant permission for external or destructive actions.
