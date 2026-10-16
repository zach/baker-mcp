# Evaluation: the bridge against the command line and skill

**Verdict after two rounds: the kill criterion is met.** Across two clients, headless and
live tasks, the bridge never beat the command line and skill on tool calls (it took 2 to 3
times as many in every group), and never beat it on success beyond one run of noise. See
"Round 2" below. Round 1's numbers are unchanged.

## Round 1

Plan A, step 3, run on 2026-10-16 against baker-dev 621fcd3 (stacks built Debug).

**Result: the kill criterion is met.** The bridge did not beat the command line and skill
on tool calls (8.5 against 4.9 a run) or on success (28/36 against 31/36). It also used more
tokens (124k against 82k a run) and the same wall time.

## Protocol

- **Tasks** (`tasks.py`): twelve, across all seven stacks. Each plants one fault in a
  fresh copy of the stack's data (`default.dta`, or Ledger's generated `economy.dta`) and
  gives the agent a person's complaint ("the easy CPU blocks things nobody could react
  to"). Every fault was checked to fail the stack's objectives while `check` passes.
- **Arms.** Both: the same model, the stack's agent skill (`stacks-agent/SKILL.md`) in the
  system prompt, the task's complaint, at most 60 turns, the stack's directory as the
  working directory, headless Claude Code (`claude -p`).
  - `cli`: Bash, Read, Write, Edit, Glob, Grep; `./game` is the binary with `--data`.
  - `bridge`: this server's eight tools, plus Read, Glob, Grep (no shell, no writes but
    `baker_propose`). No running game, so the live tools were unused.
- **Runs:** three per task per arm, 72 in all, six at a time (`harness.py`).
- **Success** is judged afterwards by the stack, not the agent: `check` exits 0,
  `sim --seeds 1-3` exits 0 over every scenario, and every file in `data/` but
  `agent.dta`, and every file in `metrics/`, is byte for byte as planted.
- **Recorded** (`results.csv`): success and its parts, tool calls, turns, tokens (input,
  output, cache read, cache write), cost, wall time.

## Results

See `summary.md` for the per-task table.

| arm | success | calls (mean) | tokens, all (mean) | wall (mean) | cost (total) |
|---|---|---|---|---|---|
| cli | 31/36 | 4.9 | 82k | 104 s | $2.15 |
| bridge | 28/36 | 8.5 | 124k | 104 s | $3.24 |

- **Every failure is the same kind**, in both arms: the planted fault was fixed, but the
  fix moved a different objective out of its band on one of seeds 1-3 (Duel's
  `normal_vs_combo` or `hard_vs_combo` win rates in 12 of 13 failures, Contraption's
  catapult in one). No run edited `default.dta`, a generated file or `metrics/`, and no
  run's final `check` failed.
- **The bridge lost most on Duel's frame data** (`duel-block` 0/3 against 2/3,
  `duel-infinite` 0/3 against 1/3). The skill tells the agent to read Duel's frame table and
  combo route through `eval`; the bridge has no `eval`, by the plan's design. That is a
  plausible cause, not one these runs prove.
- **Why the CLI needs fewer calls:** a shell call does several things at once (an agent's
  first call typically lists the directories, prints the reference, the metrics and
  scenarios, and runs the baseline `sim`). Each bridge tool does one thing, and reading
  the stack's files is a call per file. Fewer, composite tools was the plan's own remedy
  for context crowding (critique A2); it does not reduce calls against a shell.
- **Tokens** follow the calls: each call re-sends the conversation, so more calls cost more
  cache reads. Output tokens are close (1.9k against 1.7k).

## Limits of this run

- One client (Claude Code) and one model. The plan's acceptance asks for a second client;
  not run.
- Three runs per cell: one run is a third of a cell's success rate. The success gap (3
  runs of 36) is within what that noise allows; the call gap (every task, both medians) is
  not.
- Headless tasks only. The bridge's distinct value in the plan, a persistent session with
  a running game (`baker_ab`, `baker_session`, live `baker_explain`), is not exercised by
  these tasks, because the stacks' objectives are judged headless. Tasks that need a live
  game would need a person, or a scripted person, in the loop.
- `baker_propose` has no pre-apply check: Baker's planned layer check (E5) does not exist
  yet, so the candidate is written, checked, and restored on failure. A running game that
  reloads files can see a failing candidate for the length of one `check`. No run here had
  a running game.

## Reproducing

```
cmake -S stacks -B build-stacks -G Ninja -DCMAKE_BUILD_TYPE=Debug && cmake --build build-stacks  # in baker-dev
python3 eval/harness.py --baker-dev PATH --runs 3 --jobs 6 --model MODEL --work DIR
python3 eval/summarize.py > eval/summary.md
```

## Round 2

Run on 2026-10-16 at the owner's request, against the same baker-dev commit, with the same
protocol, model and success judge as round 1. Results: `results-2.csv` (180 runs), per task
in `summary-2.md`. It adds three things round 1 lacked.

1. **Live tasks** (`tasks_live.py`, six). A person's game is running headless with a
   loopback console; the harness makes the person's live edits there before the agent
   starts. Four tasks ask the agent to keep the person's live tuning (or only the part that
   passes the objectives); two ask for an A/B in the game: a snapshot named `before`, the
   fix, the game left showing the fix, the person's own tuning kept. The judge also reads
   the running game, and restores `before` to check it. Each task was checked with a
   hand-written solution first. The CLI arm gets the same game and `console.py`; the bridge
   arm gets `baker_session`, live `baker_explain` and `baker_ab`.
2. **A second client: opencode** (1.19.1, MIT, headless `opencode run`), on the owner's
   Anthropic API key, with the same model as Claude Code. Both arms, all eighteen tasks.
   Its arms mirror Claude Code's: the CLI arm has bash, read, edit, write, glob, grep; the
   bridge arm has the eight tools plus read, glob, grep. Both are confined to the stack's
   directory.
3. **A third arm, bridge + eval** (Claude Code, the twelve headless tasks): the bridge with
   an added `baker_eval` (`--with-eval`, off by default), to test whether the missing
   `eval` caused round 1's Duel losses. This changes the plan's design, so it is evidence,
   not a decision.

| client | tasks | arm | success | calls (mean) | tokens (mean) | wall (mean) | cost |
|---|---|---|---|---|---|---|---|
| Claude Code | live | cli | 15/18 | 4.4 | 70k | 51 s | $1.22 |
| Claude Code | live | bridge | 14/18 | 13.2 | 183k | 100 s | $1.76 |
| opencode | live | cli | 17/18 | 8.0 | 162k | 148 s | $1.88 |
| opencode | live | bridge | 18/18 | 17.4 | 254k | 176 s | $2.19 |
| opencode | headless | cli | 33/36 | 6.0 | 120k | 134 s | $3.18 |
| opencode | headless | bridge | 33/36 | 11.9 | 225k | 116 s | $4.94 |
| Claude Code | headless | bridge + eval | 30/36 | 9.3 | 104k | 113 s | $2.60 |
| *Claude Code (round 1)* | *headless* | *cli* | *31/36* | *4.9* | *82k* | *104 s* | *$2.15* |
| *Claude Code (round 1)* | *headless* | *bridge* | *28/36* | *8.5* | *124k* | *104 s* | *$3.24* |

Round 2 cost $17.78 in all.

### What it shows

- **Tool calls: the bridge loses everywhere**, by 2 to 3 times, in both clients, on live
  tasks as on headless ones. The live tasks did not change that: reading the session,
  snapshotting and checking are separate bridge calls, where a shell agent sends several
  console commands in one call.
- **Success: no difference beyond noise.** Live: Claude Code 15 to 14 for the CLI, opencode
  18 to 17 for the bridge. Headless, opencode: 33 to 33.
- **One live task's expected answer is contestable.** In `live-duel-keep-some` the judge
  expects the person's `hit_pause 8` to be kept: it passes on seeds 1-3, the judge's seeds.
  On seeds 1-10, as the skill's loop runs, it fails one seed of `normal_vs_combo`, and five
  agents dropped it for that reason (Claude Code CLI 3, bridge 1; opencode CLI 1). The skill
  also says one seed outside a band is noise, so either answer is defensible. Not counting
  that one value: Claude Code live CLI 18/18, bridge 15/18; opencode live CLI 18/18, bridge
  18/18. The verdict is the same either way.
- **The bridge's real live failures** were keeping the person's `jab.damage 45`, which fails
  objectives on every seed range (Claude Code bridge, twice), and one A/B whose fix moved a
  Duel win rate (`live-duel-ab`).
- **Bridge + eval did not settle round 1's question.** On the two Duel frame-data tasks it
  got 2/6, against 0/6 for the bridge and 3/6 for the CLI in round 1; over the twelve tasks
  30/36 against 28/36 and 31/36. Its failures are the same kind as every arm's (the fix moves
  a Duel win rate out of band). Eval may help a little; three runs a cell cannot show it, and
  it costs more calls (9.3).
- **Every failure in round 2 is a judged outcome**, as in round 1: no run touched
  `default.dta`, a generated file or `metrics/`, no final `check` failed, and every agent run
  ended normally.

### Found along the way

- **The live journal's times were negative** (`time_ns`), which breaks `{config.journal
  SINCE}`. The Baker session reports it fixed in baker-dev (D160, commit 947b265 on branch
  `check-gate`): the stacks' file clock wrapped past 2^63. Not verified here; no task
  depended on `since_ns`, so the runs keep the pinned commit.
- **A headless game uses a full CPU core** while it waits (requirement 0006). Live runs were
  limited to two at a time on this 4-core machine; wall times of live runs include that.
- **Two harness faults were found and fixed before any counted run:** opencode waited on an
  open stdin, and took its project from the inherited `PWD`, so a first pilot ran outside
  the stack (in this repository) with its tools unrestricted. That pilot was discarded.

### Limits

- Still three runs a cell; the success comparisons are within noise, the call gap is not.
- Two clients, one model. opencode's numbers include its own prompt and tool overhead,
  which is why both of its arms cost more than Claude Code's.
- The live tasks are headless games standing in for a person's: no one played, so how the
  A/B looked to a person is not judged.

### Reproducing round 2

```
python3 eval/harness.py --baker-dev PATH --model MODEL --set live --arms cli,bridge --jobs 2 --results R
python3 eval/harness.py --baker-dev PATH --model MODEL --set headless --arms bridge_eval --jobs 3 --results R
BAKER_EVAL_ANTHROPIC_KEY=... python3 eval/harness.py --baker-dev PATH --model MODEL --client opencode \
    --opencode PATH/opencode --set live|headless --arms cli,bridge --results R
python3 eval/summarize.py eval/results-2.csv > eval/summary-2.md
```
