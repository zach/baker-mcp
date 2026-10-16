# Evaluation: the bridge against the command line and skill

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
