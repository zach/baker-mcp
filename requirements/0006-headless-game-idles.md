# 0006: A headless game that waits for its console without using a whole core

## The need

The stacks' game started with `--headless` and a console port, for a tool to talk to, runs
its frame loop as fast as it can: one CPU core stays near 100% for as long as it runs,
whether or not anything is happening. A host that keeps a headless game open for a session
of tool requests needs it to pace its frames (to the fixed step rate, or to a rate the host
gives) or to sleep until its console has a request, so that an idle game costs next to
nothing.

## Why

A headless game held open is how a tool works against "the game as the person has it":
an editor's live preview, an automated test harness that drives several games at once, a CI
job that keeps one game for a suite of console checks, an agent working beside a person.
Each wants several such games on one machine, or one on a laptop, without starving the
build, the simulation runs, or the person's own game. Today four headless games fill a
four-core machine.

## Constraints

- The simulation keeps its fixed step: pacing changes when frames run, never how many
  steps a span of game time takes, so results stay the same.
- A request on the console is answered within a frame at the paced rate (tens of
  milliseconds), not delayed by a long sleep.
- The play build with a window is unchanged unless the person asks for it.

## Today

The integration limits how many live games it runs at once.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
