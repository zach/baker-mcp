"""Runs the evaluation: each task, three times with the command line and skill, three times
with the bridge, each by a headless agent; then judges each run by the stack's objectives.

    python3 eval/harness.py --baker-dev PATH [--tasks ID,...] [--arms cli,bridge] [--runs 3]
                            [--jobs 4] [--work DIR] [--model M]

Appends one row per run to eval/results.csv and keeps each run's transcript in DIR.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tasks import TASKS  # noqa: E402

HERE = Path(__file__).resolve().parent
FIELDS = ["task", "arm", "run", "success", "check_exit", "sim_exit", "untouched", "tool_calls",
          "turns", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
          "cost_usd", "wall_seconds", "stop", "note"]

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


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and (rel.startswith("metrics/") or (rel.startswith("data/") and rel != "data/agent.dta")):
            h.update(rel.encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def plant(task, baker_dev: Path, dst: Path) -> Path:
    shutil.copytree(baker_dev / "stacks" / task["stack"], dst)
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


def child_env():
    env = dict(os.environ)
    for k in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD", "CLAUDE_PID"):
        env.pop(k, None)
    return env


def run_one(task, arm, n, args):
    tag = f"{task['id']}/{arm}/{n}"
    base = args.work / task["id"] / arm / str(n)
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    stack = plant(task, args.baker_dev, base / task["stack"])
    binary = args.baker_dev / "build-stacks" / "bin" / f"stacks_{task['stack']}"
    planted = digest(stack)
    skill = (args.baker_dev / ".claude" / "skills" / "stacks-agent" / "SKILL.md").read_text()
    system = PREAMBLE[arm] + "\n\n" + skill
    prompt = task["ask"] + "\nWhen you are done, reply with a short report for the person, as the skill says."

    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns",
           str(args.max_turns), "--append-system-prompt", system, "--strict-mcp-config",
           "--no-session-persistence", "--setting-sources", "", "--permission-mode", "acceptEdits"]
    if args.model:
        cmd += ["--model", args.model]
    if arm == "cli":
        wrapper = stack / "game"
        wrapper.write_text(f'#!/bin/sh\nexec "{binary}" "$@" --data "{stack / "data"}"\n')
        wrapper.chmod(0o755)
        cmd += ["--tools", "Bash,Read,Write,Edit,Glob,Grep",
                "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]
    else:
        cfg = base / "mcp.json"
        cfg.write_text(json.dumps({"mcpServers": {"baker": {
            "command": sys.executable, "args": ["-m", "baker_mcp", "--game", str(binary), "--dir", str(stack),
                                                "--skill", str(args.baker_dev / ".claude/skills/stacks-agent/SKILL.md")],
            "env": {"PYTHONPATH": str(HERE.parent)}}}}))
        cmd += ["--mcp-config", str(cfg), "--tools", "Read,Glob,Grep",
                "--allowedTools", "mcp__baker", "Read", "Glob", "Grep"]

    t0 = time.monotonic()
    stop = "ok"
    try:
        p = subprocess.run(cmd, cwd=stack, capture_output=True, text=True, timeout=args.timeout, env=child_env())
        out = p.stdout
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stop = "timeout"
    wall = time.monotonic() - t0
    (base / "transcript.jsonl").write_text(out)

    tool_calls, result = 0, {}
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            tool_calls += sum(1 for b in ev["message"].get("content", []) if b.get("type") == "tool_use")
        elif ev.get("type") == "result":
            result = ev
    if result.get("subtype") not in (None, "success"):
        stop = result.get("subtype")
    u = result.get("usage", {})
    check_exit, sim_exit, sim_tail = judge(binary, stack)
    untouched = digest(stack) == planted
    (base / "judge.txt").write_text(f"check {check_exit}\nsim {sim_exit}\nuntouched {untouched}\n\n{sim_tail}")
    (base / "report.md").write_text(result.get("result", ""))
    row = dict(task=task["id"], arm=arm, run=n, success=int(check_exit == 0 and sim_exit == 0 and untouched),
               check_exit=check_exit, sim_exit=sim_exit, untouched=int(untouched), tool_calls=tool_calls,
               turns=result.get("num_turns", ""), input_tokens=u.get("input_tokens", ""),
               output_tokens=u.get("output_tokens", ""), cache_read_tokens=u.get("cache_read_input_tokens", ""),
               cache_write_tokens=u.get("cache_creation_input_tokens", ""),
               cost_usd=round(result.get("total_cost_usd", 0) or 0, 4), wall_seconds=round(wall, 1), stop=stop, note="")
    print(tag, "success" if row["success"] else "FAIL", row["tool_calls"], "calls", row["wall_seconds"], "s", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baker-dev", type=Path, required=True)
    ap.add_argument("--tasks", default="")
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
    wanted = set(filter(None, args.tasks.split(",")))
    jobs = [(t, a, n) for n in range(args.first_run, args.first_run + args.runs)
            for t in TASKS if not wanted or t["id"] in wanted for a in args.arms.split(",")]
    new = not args.results.exists() or args.results.stat().st_size == 0
    with args.results.open("a", newline="") as f, ThreadPoolExecutor(args.jobs) as pool:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for row in pool.map(lambda j: run_one(*j, args), jobs):
            w.writerow(row)
            f.flush()


if __name__ == "__main__":
    main()
