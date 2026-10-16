# 0003: A promotion preview a person can review and apply as a patch

## The need

`promote` without `--write` prints one line per path the agent layer sets: the path, the
value below, the new value, and the agent layer's file and line. A host needs, without
writing anything, the exact change `promote --write` would make to the target layer's
files, as a unified diff against those files (paths relative to the data directory), so
that a person can read it in a review tool and apply it with standard tools, and get the
same files `--write` would have written.

## Why

Promotion is a person's decision. The person decides best from the change as it will land:
the lines of `default.dta` that change, with their comments and layout, which is what a
pull request shows. Anyone who stages a change for review (an agent, a tuning tool, a
designer's batch edit, CI that opens a pull request) wants the same artifact, and today
each would have to run `--write` on a copy of the data and diff it themselves, which means
running the write path to show a preview.

## Constraints

- No file is written, created or locked: the preview is computed in memory.
- Applying the diff gives byte for byte the files `--write` writes, so the review is of
  the real change.
- Refusals (`--write` would refuse a value) are reported as they are today, and the diff
  then covers only what would be written, or nothing, as `--write` would do.
- Deterministic: the same data gives the same diff.

## Today

The integration saves `promote`'s text preview to a file for a person to read. It is not
a patch: the person still runs `promote --write` themselves to make the change.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
