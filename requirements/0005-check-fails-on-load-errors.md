# 0005: `check` fails when the data does not load cleanly, and sees into script functions

## The need

1. When loading the data reports a problem that the play loop also reports, such as a
   command run by `#autorun` that fails (a call to something that is not a function), the
   stacks' `check` prints the message to standard error and still exits 0, with nothing in
   its JSON. A host needs `check` to fail in that case and to list the problem in its JSON,
   located by file and line like any other error.
2. A call to an undefined function inside a script function's body (a `{func ...}` that
   a data file defines through `#autorun`) is not reported as demand, while the same call in
   a value is. A host needs the same rule for both: an undefined, unstubbed call anywhere in
   the data the check reads is demand.
3. A file that does not parse ends `check` with exit status 2 and no JSON. A host needs the
   parse error in the JSON too, so one reader handles every outcome.

## Why

`check` is the gate an edit must pass before it is kept: in the stacks' skill, in a
pre-commit hook, in CI, and in any tool that proposes changes to a layer. A gate that passes
data which then fails when the game loads it lets the broken edit through to the person
playing; one that skips function bodies lets through the most common agent mistake, a
misspelled function in a helper. A single JSON shape for "parsed and failed", "did not
parse" and "passed" lets every gate report the reason the same way.

## Constraints

- Messages the load already produces are reused, not re-derived: the JSON reports what the
  game would report.
- Same ordering and determinism as the rest of the report; additions are a new minor
  schema version.
- The exit status keeps its meanings; only the cases above move from 0 to 1.

## Today

The integration returns `check`'s standard error beside its JSON and tells the agent to
read it even when the exit status is 0. A proposal that loads with an error is kept.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
