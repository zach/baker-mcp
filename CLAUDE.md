# Working on this integration

This repository integrates Baker with MCP. Baker is MIT-licensed and must stay free of
MCP's terms; baker-dev's `INTEGRATIONS.md` is the policy. For work here:

- **Nothing from this repository goes into Baker.** Do not copy code, identifiers, comments,
  structure or documentation from here, or from MCP, into baker-dev or zach/baker, and do
  not write Baker code from memory of MCP's.
- **A need goes to Baker as a requirement note,** in `requirements/`, from
  `requirements/0000-template.md`, written in Baker's terms: what a host needs, why as a
  general use case, and the constraints. The owner takes the note's text to Baker.
- **Confidential material stays here.** What MCP's SDK or agreement discloses does not go
  into a requirement note, a Baker issue, a pull request, or a Baker session.
- **Do not start Baker work from this session.** Changes to Baker happen in a separate
  session in baker-dev, from the note alone.
- **Use Baker as a user would:** a released version, through its public headers. A
  workaround for a Baker limit lives here until Baker ships the feature.

## This integration

- **The server is thin.** Every tool is a command to the game binary (`check`, `reference
  --json`, `sim`, `diff`, `promote`) or a request, `(ID {command})`, to the game's loopback
  console. Each tool returns the JSON Baker wrote. Do not reimplement Baker's semantics
  here. If a tool needs something Baker does not give, write a requirement.
- **Writes.**
  - It never promotes. `baker_promote_preview` writes a patch file for a person to apply.
  - `baker_propose` writes only to the agent layer, and only after the candidate passes
    `check`.
- **The console runs any command it is sent.** Connect only to 127.0.0.1.
- **Measure.** The plan's evaluation compares this server with the command line and skill
  on the stacks' tasks. Keep the numbers in `eval/`.
