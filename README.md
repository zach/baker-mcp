# Baker for MCP

An integration of [Baker](https://github.com/zach/baker) with the
[Model Context Protocol](https://modelcontextprotocol.io): an MCP server that gives any
MCP-capable agent client a Baker game's tools.

- **The vocabulary:** the game's functions, tweaks and shapes.
- **`check`:** errors and calls to undefined functions in the data.
- **`explain`:** each value with every layer that sets it.
- **The agent layer:** proposals there are checked before they take effect.
- **Scenario runs and A/B in the running game.**
- **A promote preview:** written as a patch file, never applied.

It holds no Baker semantics of its own. Every tool is a command to the game's binary, or a
request to its loopback console, and returns the JSON Baker wrote, unchanged:
`baker.check/1`, `baker.reference/1`, `baker.tweaks/1`, `baker.shapes/1`,
`baker.reply/1`.

The plan this repository follows is plan A of baker-dev's `dev/integration-plans.md`.

## License

This repository is licensed under the MIT License (`LICENSE`). The Model Context Protocol
is an open specification. Baker itself is MIT-licensed and is used here as a dependency.
Nothing in this repository is part of Baker.

The Model Context Protocol and its SDKs are the work of their owners, who have not
endorsed this project.

## Building

The server drives a Baker game's binary. Baker is fetched at a released version:

```cmake
include(FetchContent)
FetchContent_Declare(baker GIT_REPOSITORY https://github.com/zach/baker.git GIT_TAG vX.Y.Z)
FetchContent_MakeAvailable(baker)
```

## Running

```
pip install -e .
baker-mcp --game PATH/stacks_duel --dir PATH/stacks/duel [--port 4567] [--skill PATH/SKILL.md]
```

`--dir` is the game's directory (data/, sim/, metrics/); every command is given its
`data/`. `--port` is a running game's console, started with `--console-port`; the server
connects only to 127.0.0.1. Tests: `pytest`; set `BAKER_STACKS` to a baker-dev checkout
with its stacks built to run them against the real games. The evaluation is in `eval/`.

No Baker release has the commands this server drives yet; it is tested against baker-dev
621fcd3.

## Requirements for Baker

When this integration needs something Baker lacks, write it down in `requirements/` from
`requirements/0000-template.md`, in Baker's own terms. Only the text of a requirement goes
to Baker.
