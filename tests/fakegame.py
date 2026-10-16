#!/usr/bin/env python3
"""A stand-in for a Baker game binary, for testing the server's plumbing.

It speaks the commands and console framing the server relies on. It knows nothing of
Baker's semantics; its outputs are shaped only enough to be told apart.
"""
import json
import re
import socket
import sys
from pathlib import Path

AGENT = Path("data/agent.dta")


def agent_text():
    return AGENT.read_text() if AGENT.exists() else ""


def check():
    errors = [{"message": "call to undefined function"}] if "undefined_fn" in agent_text() else []
    print(json.dumps({"format": "baker.check/1", "errors": errors}))
    return 1 if errors else 0


def reply(rid, command, state):
    name, _, arg = command.partition(" ")
    if name == "config.toggle":
        state["agent"] = not state["agent"]
        value = {"agent": state["agent"]}
    elif name in ("config.snapshot", "config.restore"):
        value = {name.split(".")[1]: arg}
    else:
        value = {"command": name, "arg": arg}
    return json.dumps({"format": "baker.reply/1", "id": rid, "ok": True, "value": value})


def console(port):
    state = {"agent": True}
    srv = socket.create_server(("127.0.0.1", port))
    print("console ready", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn, conn.makefile("rw", encoding="utf-8", newline="\n") as f:
            for line in f:
                m = re.fullmatch(r"\((\d+) \{(.*)\}\)\s*", line)
                if not m:
                    f.write(json.dumps({"format": "baker.reply/1", "ok": False}) + "\n\n")
                elif m.group(2) == "quit":
                    return 0
                else:
                    f.write(reply(int(m.group(1)), m.group(2), state) + "\n\n")
                f.flush()


def main(argv):
    if "--console-port" in argv:
        return console(int(argv[argv.index("--console-port") + 1]))
    cmd, args = argv[0], argv[1:]
    if cmd == "reference":
        print(json.dumps({"baker.reference/1": {}, "baker.tweaks/1": {}, "baker.shapes/1": {}}))
    elif cmd == "check":
        return check()
    elif cmd == "eval":
        print(f"explain (text): {args[0]}")
    elif cmd == "sim":
        out = Path(args[args.index("--out") + 1])
        out.mkdir(parents=True)
        passed = "fail" not in agent_text()
        (out / "result.json").write_text(json.dumps({"passed": passed, "args": args}))
        print(json.dumps({"passed": passed, "args": args}))
        return 0 if passed else 1
    elif cmd == "diff":
        print(json.dumps({"diff": [args[0], args[1]]}))
    elif cmd == "promote":
        if "--write" in args:
            Path("PROMOTED").write_text("never")
            return 9
        print("--- a/data/default.dta\n+++ b/data/default.dta\n" + agent_text())
    else:
        print(f"unknown command {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
