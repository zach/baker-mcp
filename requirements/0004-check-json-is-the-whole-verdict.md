# 0004: `check`'s JSON holds every reason it fails

## The need

The stacks' `check` command exits 1 for three reasons: an error in the check report, a call
to a function nothing defines (not a stub), and a shape error in the merged data (a value
out of range or of the wrong type). Only the first two are in the JSON it prints; shape
errors and shape warnings (a field no shape declares) are printed to standard error as
text. A host needs every reason for the exit status in the one JSON document: shape errors
and warnings with their path, file, line and message, in the same problem form as the
report's errors, and a field saying whether the check passed by the command's own rule.

## Why

A tool that gates an edit on `check` (an agent proposing a value, a pre-commit hook, CI)
reads the JSON to tell the author what to fix. Today a value out of range fails the check
with no error in the JSON, so the tool shows "failed" and nothing to fix unless it also
scrapes the text on standard error. Shape warnings are how a designer's request for a word
the game lacks shows up, which a tool would like to collect as it collects demand.

## Constraints

- The existing fields keep their meaning; this adds fields in a new minor version, as the
  schema's versioning rules allow.
- Sorted and deterministic like the rest of the report.
- The pass field states the command's rule, so a reader need not re-derive it from demand
  and stubs.

## Today

The integration returns the JSON and, beside it, the text the command wrote to standard
error, and the exit status. An agent reads the text to find a shape error.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
