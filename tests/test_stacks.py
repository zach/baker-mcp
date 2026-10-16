"""The server against baker-dev's real stacks.

Set BAKER_STACKS to a baker-dev checkout whose stacks are built (build-stacks/bin). These
tests are skipped without it. They copy each stack's directory and point the game at the
copy (--data), so the stacks' own data is never written.
"""
import json
import os
import shutil
from pathlib import Path

import pytest

from baker_mcp.server import Game
from conftest import call, call_json, free_port, read, start_console

ROOT = Path(os.environ["BAKER_STACKS"]) if os.environ.get("BAKER_STACKS") else None
pytestmark = pytest.mark.skipif(ROOT is None, reason="BAKER_STACKS is not set")

BROKEN = "#autorun {func agent.broken () {not_a_function_anywhere}}\n"


def stack(name, tmp_path):
    dst = tmp_path / name
    shutil.copytree(ROOT / "stacks" / name, dst)
    return Game(binary=ROOT / "build-stacks" / "bin" / f"stacks_{name}", directory=dst,
                skill=ROOT / ".claude" / "skills" / "stacks-agent" / "SKILL.md")


@pytest.mark.parametrize("name", ["cube", "duel"])
def test_headless(name, tmp_path):
    g = stack(name, tmp_path)
    v = call_json(g, "baker_vocabulary")
    assert set(v) == {"reference", "tweaks", "shapes"}
    assert v["reference"]["schema"] == "baker.reference/1"
    c = call_json(g, "baker_check")
    assert c["exit"] == 0 and c["check"]["schema"] == "baker.check/1", c["log"]

    agent = g.directory / "data" / "agent.dta"
    before = agent.read_bytes() if agent.exists() else None
    r = call_json(g, "baker_propose", text=BROKEN)
    assert r["kept"] is False and r["exit"] == 1
    assert "not_a_function_anywhere" in json.dumps(r["check"]["demand"])
    assert (agent.read_bytes() if agent.exists() else None) == before

    run = call_json(g, "baker_run", seeds="1-2")
    assert run["exit"] in (0, 1) and "(summary" in run["output"], run["output"]
    again = call_json(g, "baker_run", seeds="1-2", before=run["out"])
    assert again["before"] and again["exit"] == run["exit"]

    p = call_json(g, "baker_promote_preview")
    assert (g.directory / p["file"]).read_text() == p["preview"]
    assert "baker.reference/1" in read(g, "baker://vocabulary")
    assert "stacks-agent" in read(g, "baker://skill")


def test_cube_explain_headless(tmp_path):
    g = stack("cube", tmp_path)
    err, text = call(g, "baker_explain", path="cube.spin")
    assert not err, text


def test_live_cube(tmp_path):
    g = stack("cube", tmp_path)
    g.port = free_port()
    proc = start_console([str(g.binary), "--headless", "--frames", "100000000", "--console-port",
                          str(g.port), "--data", str(g.directory / "data")], g.directory, g.port)
    try:
        r = call_json(g, "baker_explain", path="cube.spin")
        assert r["schema"] == "baker.reply/1" and r["ok"], r
        s = call_json(g, "baker_session")
        assert set(s) == {"journal", "unsaved", "loop"} and all(v["ok"] for v in s.values()), s
        assert call_json(g, "baker_ab", action="snapshot", name="t0")["ok"]
        t = call_json(g, "baker_ab", action="toggle")
        assert t["ok"], t
        assert call_json(g, "baker_ab", action="restore", name="t0")["ok"]
        assert not call_json(g, "baker_ab", action="restore", name="nope")["ok"]
    finally:
        proc.kill()
        proc.wait()
