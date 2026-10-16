"""Runs the evaluation: each task by a headless agent, per client and arm, judged afterwards
by the stack's own objectives (and, for live tasks, by the running game).

    python3 eval/harness.py --baker-dev PATH [--set headless|live] [--tasks ID,...]
        [--client claude|opencode] [--arms cli,bridge,bridge_eval] [--runs 3] [--jobs 4]
        [--work DIR] [--model M] [--results FILE]

Appends one row per run to the results file and keeps each run's transcript in DIR. The
first run (results.csv) used the defaults: --set headless --client claude --arms cli,bridge.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tasks import TASKS  # noqa: E402
from tasks_live import TASKS_LIVE  # noqa: E402

HERE = Path(__file__).resolve().parent
FIELDS = ["task", "arm", "run", "success", "check_exit", "sim_exit", "untouched", "tool_calls",
          "turns", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
          "cost_usd", "wall_seconds", "stop", "note"]
FIELDS2 = ["client", "set"] + FIELDS + ["values_ok", "live_ok"]

PREAMBLE = {
    "cli": """You work on a Baker game stack from the command line. The stack (its data/, sim/,
metrics/) is the current directory. `./game` is its binary, already pointed at this
directory's data: where the skill below says `$G`, run `./game` (for example
`./game check`, `./game sim --seeds 1-3`). Edit only data/agent.dta (and sim/ if you need a
scenario). Never edit data/default.dta or any other file in data/.""",
    "bridge": """You work on a Baker game stack through the `baker` MCP tools. The stack (its data/,
sim/, metrics/) is the current directory; you may read its files. The skill's commands are
these tools: `$G reference --json` is baker_vocabulary, `$G check` is baker_check, `$G sim`
is baker_run, `$G promote` is baker_promote_preview, and {config.explain PATH} is
baker_explain. You change data only through baker_propose, which replaces data/agent.dta and
keeps it only if check passes. There is no shell, and no `eval` command.""",
}

PREAMBLE["bridge_eval"] = PREAMBLE["bridge"].replace(
    "There is no shell, and no `eval` command.",
    "`$G eval \"{cmd}\"...` is baker_eval. There is no shell.")

LIVE = {
    "cli": """A person has the game running now. Its console is on 127.0.0.1:{port}; send it commands
with `python3 -I {console} --port {port} "{{cmd}}"` (add --json for the raw replies). The
console has Baker's Config tools: {{config.explain PATH}}, {{config.journal}},
{{config.unsaved}}, {{config.get PATH}}, {{config.toggle LAYER}}, {{config.snapshot NAME}},
{{config.restore NAME}}, {{config.layers}}. The running game reloads data/agent.dta when it
changes. Edits the person made live are in the game only, not in any file.""",
    "bridge": """A person has the game running now; the tools reach it: baker_session (the person's live
edits: journal, unsaved, loop), baker_explain (from the running game), baker_ab (toggle the
agent layer, snapshot, restore). The running game reloads data/agent.dta when it changes.
Edits the person made live are in the game only, not in any file.""",
}
LIVE["bridge_eval"] = LIVE["bridge"]


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and (rel.startswith("metrics/") or (rel.startswith("data/") and rel != "data/agent.dta")):
            h.update(rel.encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def plant(task, baker_dev: Path, dst: Path) -> Path:
    shutil.copytree(baker_dev / "stacks" / task["stack"], dst)
    if "file" in task:
        f = dst / task["file"]
        text = f.read_text()
        assert text.count(task["old"]) == 1, task["id"]
        f.write_text(text.replace(task["old"], task["new"]))
    return dst


def judge(binary: Path, stack: Path):
    data = str(stack / "data")
    c = subprocess.run([binary, "check", "--data", data], capture_output=True, text=True, timeout=600)
    s = subprocess.run([binary, "sim", "--seeds", "1-3", "--data", data], capture_output=True, text=True,
                       timeout=1800)
    return c.returncode, s.returncode, s.stdout[-3000:]


def headless_get(binary: Path, stack: Path, paths):
    cmds = [f"{{config.get {p}}}" for p in paths]
    out = subprocess.run([binary, "eval", *cmds, "--data", str(stack / "data")], capture_output=True,
                         text=True, timeout=600).stdout.splitlines()
    return dict(zip(paths, out))


def same(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


class Console:
    """The person's side of the running game: one loopback connection, Baker's requests."""

    def __init__(self, port):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=30)
        self.n = 0

    def ask(self, cmd):
        self.n += 1
        self.sock.sendall(f"(p{self.n} {{{cmd}}})\n".encode())
        buf = b""
        while not buf.endswith(b"\n\n"):
            chunk = self.sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        return json.loads(buf.decode().strip())

    def get(self, path):
        r = self.ask(f"config.get {path}")
        return r.get("text") if r.get("ok") else None


def start_game(binary: Path, stack: Path):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen([binary, "--headless", "--frames", "100000000", "--console-port", str(port),
                             "--data", str(stack / "data")], cwd=stack, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    for _ in range(300):
        try:
            return proc, port, Console(port)
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError("game exited")
            time.sleep(0.1)
    raise RuntimeError("console never opened")


def child_env():
    env = dict(os.environ)
    for k in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD", "CLAUDE_PID",
              "BAKER_EVAL_ANTHROPIC_KEY"):
        env.pop(k, None)
    return env


def server_args(args, binary, stack, arm, port):
    a = ["-m", "baker_mcp", "--game", str(binary), "--dir", str(stack),
         "--skill", str(args.baker_dev / ".claude/skills/stacks-agent/SKILL.md")]
    if port:
        a += ["--port", str(port)]
    if arm == "bridge_eval":
        a.append("--with-eval")
    return a


def run_claude(args, arm, base, stack, binary, system, prompt, port):
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns",
           str(args.max_turns), "--append-system-prompt", system, "--strict-mcp-config",
           "--no-session-persistence", "--setting-sources", "", "--permission-mode", "acceptEdits"]
    if args.model:
        cmd += ["--model", args.model]
    if arm == "cli":
        cmd += ["--tools", "Bash,Read,Write,Edit,Glob,Grep",
                "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]
    else:
        cfg = base / "mcp.json"
        cfg.write_text(json.dumps({"mcpServers": {"baker": {
            "command": sys.executable, "args": server_args(args, binary, stack, arm, port),
            "env": {"PYTHONPATH": str(HERE.parent)}}}}))
        cmd += ["--mcp-config", str(cfg), "--tools", "Read,Glob,Grep",
                "--allowedTools", "mcp__baker", "Read", "Glob", "Grep"]
    out, stop = launch(cmd, stack, child_env(), args.timeout)
    tool_calls, result = 0, {}
    for ev in events(out):
        if ev.get("type") == "assistant":
            tool_calls += sum(1 for b in ev["message"].get("content", []) if b.get("type") == "tool_use")
        elif ev.get("type") == "result":
            result = ev
    if result.get("subtype") not in (None, "success"):
        stop = result.get("subtype")
    u = result.get("usage", {})
    return out, stop, dict(tool_calls=tool_calls, turns=result.get("num_turns", ""),
                           input_tokens=u.get("input_tokens", ""), output_tokens=u.get("output_tokens", ""),
                           cache_read_tokens=u.get("cache_read_input_tokens", ""),
                           cache_write_tokens=u.get("cache_creation_input_tokens", ""),
                           cost_usd=round(result.get("total_cost_usd", 0) or 0, 4)), result.get("result", "")


def run_opencode(args, arm, base, stack, binary, system, prompt, port):
    home = base / "home"
    home.mkdir()
    (base / "system.md").write_text(system)
    off = ["webfetch", "websearch", "task", "todowrite", "todoread", "codesearch", "skill"]
    if arm != "cli":
        off += ["bash", "edit", "write", "patch", "multiedit", "apply_patch"]
    cfg = {"$schema": "https://opencode.ai/config.json", "model": f"anthropic/{args.model}",
           "autoupdate": False, "share": "disabled", "instructions": [str(base / "system.md")],
           "tools": {t: False for t in off},
           "permission": {"edit": "deny" if arm != "cli" else "allow",
                          "bash": "deny" if arm != "cli" else "allow", "webfetch": "deny"}}
    if arm != "cli":
        cfg["mcp"] = {"baker": {"type": "local", "enabled": True,
                                "command": [sys.executable, *server_args(args, binary, stack, arm, port)],
                                "environment": {"PYTHONPATH": str(HERE.parent)}}}
    (stack / "opencode.json").write_text(json.dumps(cfg, indent=1))
    env = child_env()
    env.update(HOME=str(home), ANTHROPIC_API_KEY=os.environ["BAKER_EVAL_ANTHROPIC_KEY"],
               OPENCODE_DISABLE_AUTOUPDATE="1")
    cmd = [args.opencode, "run", "--format", "json", "-m", f"anthropic/{args.model}", "--auto", prompt]
    out, stop = launch(cmd, stack, env, args.timeout)
    (stack / "opencode.json").unlink(missing_ok=True)
    calls, steps, tok, cost, text = 0, 0, dict(i=0, o=0, r=0, w=0), 0.0, ""
    for ev in events(out):
        part = ev.get("part", {})
        if ev.get("type") == "tool_use":
            calls += 1
        elif ev.get("type") == "step_finish":
            steps += 1
            t = part.get("tokens", {})
            tok["i"] += t.get("input", 0)
            tok["o"] += t.get("output", 0) + t.get("reasoning", 0)
            tok["r"] += t.get("cache", {}).get("read", 0)
            tok["w"] += t.get("cache", {}).get("write", 0)
            cost += part.get("cost", 0) or 0
        elif ev.get("type") == "text":
            text = part.get("text", text)
        elif ev.get("type") == "error":
            stop = "error"
    return out, stop, dict(tool_calls=calls, turns=steps, input_tokens=tok["i"], output_tokens=tok["o"],
                           cache_read_tokens=tok["r"], cache_write_tokens=tok["w"],
                           cost_usd=round(cost, 4)), text


def launch(cmd, cwd, env, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.stdout, "ok"
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return out, "timeout"


def events(out):
    for line in out.splitlines():
        try:
            yield json.loads(line)
        except ValueError:
            continue


def run_one(task, arm, n, args):
    tag = f"{args.client}/{task['id']}/{arm}/{n}"
    base = args.work / args.client / task["id"] / arm / str(n)
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    stack = plant(task, args.baker_dev, base / task["stack"])
    binary = args.baker_dev / "build-stacks" / "bin" / f"stacks_{task['stack']}"
    planted = digest(stack)
    skill = (args.baker_dev / ".claude" / "skills" / "stacks-agent" / "SKILL.md").read_text()
    live = "live" in task
    proc = port = console = None
    if live:
        proc, port, console = start_game(binary, stack)
        for path, value in task["live"].items():
            assert console.ask(f"config.set {path} {value}")["ok"], (tag, path)
    pre = PREAMBLE[arm]
    if live:
        pre += "\n\n" + LIVE[arm].format(port=port, console=args.baker_dev / "stacks/tools/console.py")
    system = pre + "\n\n" + skill
    prompt = task["ask"] + "\nWhen you are done, reply with a short report for the person, as the skill says."
    if arm == "cli":
        wrapper = stack / "game"
        wrapper.write_text(f'#!/bin/sh\nexec "{binary}" "$@" --data "{stack / "data"}"\n')
        wrapper.chmod(0o755)

    t0 = time.monotonic()
    try:
        run = run_claude if args.client == "claude" else run_opencode
        out, stop, stats, report = run(args, arm, base, stack, binary, system, prompt, port)
        wall = time.monotonic() - t0
        (base / "transcript.jsonl").write_text(out)
        (base / "report.md").write_text(report)

        check_exit, sim_exit, sim_tail = judge(binary, stack)
        untouched = digest(stack) == planted
        values_ok = live_ok = ""
        notes = []
        if "expect" in task:
            got = headless_get(binary, stack, list(task["expect"]))
            bad = {p: got.get(p) for p, v in task["expect"].items() if not same(got.get(p), v)}
            values_ok = int(not bad)
            if bad:
                notes.append(f"values {bad}")
        if live:
            bad = {}
            for p, v in task.get("live_expect", {}).items():
                if not same(console.get(p), v):
                    bad[p] = console.get(p)
            if "ab" in task:
                path, planted_value = task["ab"]
                want = headless_get(binary, stack, [path])[path]
                now = console.get(path)
                if not same(now, want):
                    bad["fix_on"] = f"{now} (headless {want})"
                r = console.ask("config.restore before")
                if not r.get("ok"):
                    bad["before"] = "no snapshot"
                elif not same(console.get(path), planted_value):
                    bad["before"] = console.get(path)
            live_ok = int(not bad)
            if bad:
                notes.append(f"live {bad}")
    finally:
        if proc:
            proc.kill()
            proc.wait()
    (base / "judge.txt").write_text(f"check {check_exit}\nsim {sim_exit}\nuntouched {untouched}\n"
                                    f"values {values_ok}\nlive {live_ok}\n{'; '.join(notes)}\n\n{sim_tail}")
    success = check_exit == 0 and sim_exit == 0 and untouched and values_ok in ("", 1) and live_ok in ("", 1)
    row = dict(client=args.client, set=args.set, task=task["id"], arm=arm, run=n, success=int(success),
               check_exit=check_exit, sim_exit=sim_exit, untouched=int(untouched), wall_seconds=round(wall, 1),
               stop=stop, note="; ".join(notes)[:300], values_ok=values_ok, live_ok=live_ok, **stats)
    print(tag, "success" if success else "FAIL", stats["tool_calls"], "calls", row["wall_seconds"], "s", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baker-dev", type=Path, required=True)
    ap.add_argument("--set", choices=["headless", "live"], default="headless")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--client", choices=["claude", "opencode"], default="claude")
    ap.add_argument("--opencode", default="opencode", help="the opencode binary")
    ap.add_argument("--arms", default="cli,bridge")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--first-run", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--work", type=Path, default=Path("/tmp/baker-mcp-eval"))
    ap.add_argument("--model", default="")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--results", type=Path, default=HERE / "results.csv")
    args = ap.parse_args()
    args.baker_dev = args.baker_dev.resolve()
    if args.client == "opencode" and not args.model:
        ap.error("--model is required with opencode (an Anthropic model id)")
    pool_tasks = TASKS if args.set == "headless" else TASKS_LIVE
    wanted = set(filter(None, args.tasks.split(",")))
    jobs = [(t, a, n) for n in range(args.first_run, args.first_run + args.runs)
            for t in pool_tasks if not wanted or t["id"] in wanted for a in args.arms.split(",")]
    fields = FIELDS if args.results.name == "results.csv" else FIELDS2
    new = not args.results.exists() or args.results.stat().st_size == 0
    with args.results.open("a", newline="") as f, ThreadPoolExecutor(args.jobs) as pool:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        if new:
            w.writeheader()
        for row in pool.map(lambda j: run_one(*j, args), jobs):
            w.writerow(row)
            f.flush()


if __name__ == "__main__":
    main()
