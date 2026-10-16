# 0002: Scenario results a tool can read, and a comparison of two runs

## The need

1. The stacks' `sim` command writes its results as Baker text: a line per run on standard
   output, a `(run ...)` file per scenario and seed, and a `(summary ...)`. A host needs the
   same results as one JSON document, with a schema name and version like `check`'s: each
   run (scenario, seed, steps, each objective's value, pass, and error) and the summary
   (per objective: passed, failed, min, median, max), plus the exit status's meaning.
2. A host needs to compare two such results, before and after an edit, and be told which
   objectives moved: passed to failed and back, and the change in each objective's median
   and range. As a command (`sim` given an earlier result, or a separate command over two
   result directories), in the same JSON form.

## Why

The agent loop in the stacks' skill is "baseline, change, run again, compare objective by
objective". Today every tool that drives that loop (an agent, CI, a dashboard of balance
over a milestone) compares the text itself, and each one decides separately what "moved"
means: whether a median shift counts, how a newly failing seed is reported. The comparison
is the game's judgment of its own data, so it belongs beside the objectives that define it.
A studio would also keep the JSON as a build artifact and diff it across milestones, as it
does `check`'s.

## Constraints

- The same data, scenario and seeds give the same bytes, as `check`'s JSON does: sorted by
  scenario, then seed, then objective; no times or absolute paths.
- The `.dta` results stay; the JSON is the same data, not a second judgment.
- Non-finite values are written as `check`'s and the reply's are (`null`), with the reason in
  the objective's error.
- The comparison needs no rerun: it reads two result directories.

## Today

The integration returns `sim`'s text, keeps each run's directory, and returns the earlier
run's summary file beside the new output. Telling which objectives moved is left to the
agent, which reads both summaries.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
