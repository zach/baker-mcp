"""The server against baker-dev's real stacks.

Set BAKER_STACKS to a baker-dev checkout whose stacks are built (build-stacks/bin). These
tests are skipped without it. They copy each stack's directory, so the stacks' own data
(default.dta) is never written.
"""
import os
import shutil
from pathlib import Path

import pytest

from baker_mcp.server import Game
from conftest import call, call_json, free_port, start_console

ROOT = Path(os.environ.get("BAKER_STACKS", "")) if os.environ.get("BAKER_STACKS") else None
pytestmark = pytest.mark.skipif(ROOT is None, reason="BAKER_STACKS is not set")


def stack(name, tmp_path):
    src = ROOT / "stacks" / name
    dst = tmp_path / name
    shutil.copytree(src, dst)
    return Game(binary=ROOT / "build-stacks" / "bin" / f"stacks_{name}", directory=dst)


@pytest.mark.parametrize("name", ["cube", "duel"])
def test_headless(name, tmp_path):
    g = stack(name, tmp_path)
    v = call_json(g, "baker_vocabulary")
    assert v  # the object of reference --json; its schema is checked by eye on first run
    c = call_json(g, "baker_check")
    assert not c.get("errors"), c
    r = call_json(g, "baker_propose", text="(not_a_function_anywhere {undefined_function_xyz})\n")
    assert r["kept"] is False
    assert call(g, "baker_run")[0] is False


def test_live_cube(tmp_path):
    g = stack("cube", tmp_path)
    g.port = free_port()
    proc = start_console([str(g.binary), "--headless", "--frames", "100000000", "--console-port", str(g.port)],
                         g.directory, g.port)
    try:
        s = call_json(g, "baker_session")
        assert set(s) == {"journal", "unsaved", "loop"}
        assert call(g, "baker_ab", action="snapshot", name="t0")[0] is False
        assert call(g, "baker_ab", action="restore", name="t0")[0] is False
    finally:
        proc.kill()
        proc.wait()
