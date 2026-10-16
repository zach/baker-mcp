# Evaluation: the bridge against the command line and skill

Plan A, step 3. **Status: not run.** This session could not read or build baker-dev (see
"Blocked" below), so there are no numbers yet. Nothing in `results.csv` is estimated.

## Protocol

- **Tasks:** twelve, taken from the stacks' agent skill (baker-dev
  `.claude/skills/stacks-agent/SKILL.md` and `stacks/agent.md`), each judged by the stacks'
  own objectives (`sim` exit 0), not by the agent's say-so. Candidates named by the plan:
  tune Duel's matchup spread; fix a broken Ledger price table. The other ten are chosen
  from the skill when it can be read, and listed in `tasks.md` before any run.
- **Arms:** `cli` (an agent with a shell, the game's binary and the skill text) and
  `bridge` (the same agent and prompt, with this server and no shell). Same model, same
  task prompt, same step limit.
- **Runs:** three per task per arm: 72 in all. Each run starts from a fresh copy of the
  stack's directory, so `default.dta` is never touched.
- **Recorded per run** (`results.csv`): task, arm, run, success (objectives passed), tool
  calls, input and output tokens, wall seconds, and a note.
- **Kill criterion:** if the bridge does not beat the CLI on tool calls or on success, the
  report says so plainly.

## Known difference to record

`baker_propose` writes `data/agent.dta`, runs `check`, and restores the old file when check
fails. Baker's planned pre-apply layer check (E5) does not exist yet, so a running game that
reloads changed files can see a failing candidate for the length of one `check`. The CLI
arm has the same exposure, and worse (nothing restores). Note any run where this shows.

## Blocked

The session was not granted read access to zach/baker-dev (attaching it, and a plain
clone, were both refused), so it could not build the stacks, read the interface documents
or the skill, or run the agents. To unblock: attach baker-dev with read access to the
session (or set the `BAKER_DEV_TOKEN` secret for CI), then run `pytest` with
`BAKER_STACKS` set, fill `tasks.md`, and run the protocol above.
