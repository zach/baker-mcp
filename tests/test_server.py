"""The server's plumbing, against a stand-in game binary."""
import json

from conftest import call, call_json, read


def test_tools_listed(fake):
    import asyncio

    from mcp.client import Client

    from baker_mcp.server import build

    async def go():
        async with Client(build(fake)) as c:
            return {t.name for t in (await c.list_tools()).tools}

    assert asyncio.run(go()) == {
        "baker_vocabulary", "baker_check", "baker_explain", "baker_propose",
        "baker_run", "baker_ab", "baker_session", "baker_promote_preview",
    }


def test_vocabulary_is_bakers_json(fake):
    v = call_json(fake, "baker_vocabulary")
    assert set(v) == {"reference", "tweaks", "shapes"}
    assert json.loads(read(fake, "baker://vocabulary")) == v


def test_check_returns_errors_without_failing(fake):
    (fake.directory / "data/agent.dta").write_text("(x {undefined_fn})")
    r = call_json(fake, "baker_check")
    assert r["exit"] == 1 and r["check"]["errors"] and "undefined_fn" in r["log"]


def test_explain_headless_is_text(fake):
    err, text = call(fake, "baker_explain", path="duel.spread")
    assert not err and text.startswith("explain (text): {config.explain duel.spread}")


def test_explain_refuses_non_paths(fake):
    err, _ = call(fake, "baker_explain", path="a} {quit")
    assert err


def test_propose_keeps_a_passing_candidate(fake):
    r = call_json(fake, "baker_propose", text="(spread 3)")
    assert r["kept"] and r["exit"] == 0 and r["check"]["schema"] == "baker.check/1"
    assert (fake.directory / "data/agent.dta").read_text() == "(spread 3)"


def test_propose_restores_on_failure(fake):
    agent = fake.directory / "data/agent.dta"
    agent.write_text("(spread 2)")
    r = call_json(fake, "baker_propose", text="(spread {undefined_fn})")
    assert not r["kept"] and r["check"]["errors"]
    assert agent.read_text() == "(spread 2)"


def test_propose_removes_a_new_failing_file(fake):
    r = call_json(fake, "baker_propose", text="{undefined_fn}")
    assert not r["kept"]
    assert not (fake.directory / "data/agent.dta").exists()


def test_run_and_compare(fake):
    a = call_json(fake, "baker_run", scenario="opening", seeds="1-5")
    assert a["exit"] == 0 and a["result"] == "passed" and a["before"] is None
    assert a["output"].startswith("args --scenario opening --seeds 1-5 --out")
    (fake.directory / "data/agent.dta").write_text("fail")
    b = call_json(fake, "baker_run", before=a["out"])
    assert b["exit"] == 1 and b["result"] == "failed"
    assert "(passed 1)" in b["before"] and "(passed 0)" in b["output"]


def test_run_rejects_bad_seeds_and_escapes(fake):
    assert call(fake, "baker_run", seeds="1-5; rm")[0]
    assert call(fake, "baker_run", before="../../etc")[0]
    assert call(fake, "baker_run", before="data")[0]


def test_promote_preview_writes_a_patch_and_never_promotes(fake):
    (fake.directory / "data/agent.dta").write_text("(spread 3)")
    r = call_json(fake, "baker_promote_preview")
    saved = fake.directory / r["file"]
    assert saved.parent.name == "patches" and saved.read_text() == r["preview"]
    assert r["preview"].startswith("would write into default") and "(spread 3)" in r["preview"]
    assert not (fake.directory / "PROMOTED").exists()


def test_skill_resource(fake, tmp_path):
    assert "No agent skill" in read(fake, "baker://skill")
    fake.skill = tmp_path / "SKILL.md"
    fake.skill.write_text("# the skill")
    assert read(fake, "baker://skill") == "# the skill"


def test_live_tools_without_a_game_are_errors(fake):
    assert call(fake, "baker_session")[0]
    assert call(fake, "baker_ab", action="toggle")[0]


def test_live_explain_ab_and_session(fake_live):
    r = call_json(fake_live, "baker_explain", path="duel.spread")
    assert r["schema"] == "baker.reply/1" and r["value"]["arg"] == "duel.spread"
    assert call_json(fake_live, "baker_ab", action="toggle")["value"] == {"agent": False}
    assert call_json(fake_live, "baker_ab", action="snapshot", name="before")["value"] == {"snapshot": "before"}
    assert call(fake_live, "baker_ab", action="restore", name="x y")[0]
    assert call_json(fake_live, "baker_session", since_ns=5)["journal"]["value"]["arg"] == "5"
    s = call_json(fake_live, "baker_session")
    assert {k: v["value"]["command"] for k, v in s.items()} == {
        "journal": "config.journal", "unsaved": "config.unsaved", "loop": "config.loop"}


def test_stdio_end_to_end(fake):
    """The server as a client launches it: a subprocess on stdio."""
    import asyncio
    import sys
    from pathlib import Path

    from mcp import StdioServerParameters
    from mcp.client import Client

    root = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "baker_mcp", "--game", str(fake.binary), "--dir", str(fake.directory)],
        cwd=str(root))

    async def go():
        async with Client(params) as c:
            return (await c.call_tool("baker_check", {})).content[0].text

    assert json.loads(asyncio.run(go()))["check"]["schema"] == "baker.check/1"


def test_eval_is_off_unless_asked(fake):
    err, text = call(fake, "baker_eval", commands=["{x}"])
    assert err


def test_eval_when_asked(fake):
    fake.with_eval = True
    r = call_json(fake, "baker_eval", commands=["{duel.frame_table}"], seed=3)
    assert r["exit"] == 0 and r["output"].startswith("explain (text): --seed")
    assert call(fake, "baker_eval", commands=["duel.frame_table"])[0]
