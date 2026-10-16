# 0001: Structured output for commands evaluated without a running game

## The need

A host runs one console command against a game that is not running, from the command line
(`<game> eval "{config.explain PATH}"` today), and receives the same structured reply a
running game's console gives for that command: the reply document, one line of JSON, with
the same fields and the same error form. A flag on `eval` that selects this output would
do, as would any other spelling Baker prefers.

## Why

Tools that drive a game from outside (editors, build scripts, test runners, automated
tuning) ask the same questions whether or not a game is running: where does this value come
from, which layers set it. Today they get JSON from a running game and prose from the
command line, so each such tool parses Baker's human-readable text, which is not a
contract and changes with wording. One reply format for both paths lets a tool treat a
headless game and a live one the same way, and lets CI answer the questions a person would
ask at the console.

## Constraints

- The JSON is the existing console reply document, not a second format: a reader of one
  reads the other.
- One command per invocation is enough. Exit status distinguishes "the command ran" from
  "it could not be evaluated", with the reply carrying the error in the second case.
- No window, audio or frame loop is started; it runs on a machine without a display.
- Output is deterministic for the same data, so it can be compared in tests.

## Today

The integration returns `eval`'s text unchanged when no game is running and says so in the
result; with a running game on a loopback console it returns the JSON reply. A client
therefore has to handle two shapes for one question, and the headless shape cannot be
checked by a schema.

## Not included

This note contains no code, identifiers, structure or documentation from the integration's
target, and nothing confidential.
