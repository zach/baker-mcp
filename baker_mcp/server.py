"""An MCP server that gives an agent client a Baker game's tools.

It holds no Baker semantics. Each tool runs a command of the game's binary or sends a
request to the game's loopback console, and returns the text Baker wrote, unchanged. Where
a tool adds anything (propose's kept flag, run's exit meaning), the addition wraps Baker's
text; it never rewrites it.
"""

from __future__ import annotations

import argparse
import datetime
import itertools
import json
import os
import socket
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

LOOPBACK = "127.0.0.1"  # The console runs any command it is sent: never another host.
AGENT_LAYER = Path("data") / "agent.dta"


@dataclass
class Game:
    """One Baker game: its binary, the directory it runs from, and its console port."""

    binary: Path
    directory: Path
    port: int | None = None
    skill: Path | None = None
    timeout: float = 120.0
    sim_timeout: float = 900.0
    _ids: itertools.count = field(default_factory=lambda: itertools.count(1))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # -- the binary ------------------------------------------------------------------

    def run(self, *args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [str(self.binary), *args],
                cwd=self.directory,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
        except FileNotFoundError as e:
            raise ToolError(f"game binary not found: {self.binary}") from e
        except subprocess.TimeoutExpired as e:
            raise ToolError(f"`{' '.join(args)}` timed out after {e.timeout}s") from e

    def run_ok(self, *args: str, ok: tuple[int, ...] = (0,), timeout: float | None = None) -> subprocess.CompletedProcess[str]:
        """Run a command; an exit code outside `ok` is an error carrying Baker's output."""
        p = self.run(*args, timeout=timeout)
        if p.returncode not in ok:
            raise ToolError(f"`{' '.join(args)}` exited {p.returncode}\n{p.stdout}{p.stderr}".rstrip())
        return p

    # -- the console -----------------------------------------------------------------

    def request(self, command: str) -> str:
        """Send `(ID {command})` to the console and return the reply's first line.

        A reply is one line of JSON (baker.reply/1) and then an empty line.
        """
        if self.port is None:
            raise ToolError("no running game: start the server with --port, and the game with --console-port")
        if "\n" in command:
            raise ToolError("a console command is one line")
        with self._lock:
            rid = next(self._ids)
            try:
                with socket.create_connection((LOOPBACK, self.port), timeout=self.timeout) as s:
                    s.sendall(f"({rid} {{{command}}})\n".encode())
                    f = s.makefile("r", encoding="utf-8", newline="\n")
                    lines = []
                    for line in f:
                        line = line.rstrip("\r\n")
                        if line == "":
                            break
                        lines.append(line)
            except OSError as e:
                raise ToolError(f"console at {LOOPBACK}:{self.port}: {e}") from e
        if not lines:
            raise ToolError(f"console closed without a reply to `{command}`")
        return "\n".join(lines)

    def live(self) -> bool:
        if self.port is None:
            return False
        try:
            socket.create_connection((LOOPBACK, self.port), timeout=1.0).close()
            return True
        except OSError:
            return False

    # -- files this server may write -------------------------------------------------

    def own_path(self, *parts: str) -> Path:
        """A path under the game directory, refusing any that leaves it."""
        p = (self.directory / Path(*parts)).resolve()
        if not p.is_relative_to(self.directory.resolve()):
            raise ToolError(f"path leaves the game directory: {Path(*parts)}")
        return p


def stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


class Raw(str):
    """Text Baker wrote. In `wrap` it goes in verbatim when it is JSON."""


def wrap(**parts: object) -> str:
    """Join Baker's texts into one JSON object without re-encoding them."""
    out = []
    for k, v in parts.items():
        text = json.dumps(v)
        if isinstance(v, Raw):
            try:
                json.loads(v)
                text = v.strip()
            except ValueError:
                pass
        out.append(f"{json.dumps(k)}: {text}")
    return "{" + ", ".join(out) + "}"


def build(game: Game) -> MCPServer:
    mcp = MCPServer(
        name="baker",
        instructions=(
            "Tools for a Baker game. Every result is the JSON Baker wrote. Start with "
            "baker_vocabulary, propose changes with baker_propose (checked before they are "
            "kept), measure with baker_run, compare in the running game with baker_ab."
        ),
    )

    @mcp.tool()
    def baker_vocabulary() -> str:
        """The game's functions, tweaks and shapes: `reference --json`, an object holding
        baker.reference/1, baker.tweaks/1 and baker.shapes/1."""
        return game.run_ok("reference", "--json").stdout

    @mcp.tool()
    def baker_check() -> str:
        """Check the game's data: baker.check/1 JSON. Errors are in the JSON; the call
        succeeds whether or not there are any."""
        return game.run_ok("check", ok=(0, 1)).stdout

    @mcp.tool()
    def baker_explain(path: str) -> str:
        """A config path's layer chain: each layer that sets it, and the value it has.

        From the running game (if there is one) this is baker.reply/1 JSON. Without a
        running game it is Baker's text from `eval`, not JSON."""
        if " " in path or "}" in path or "{" in path:
            raise ToolError(f"not a config path: {path!r}")
        if game.live():
            return game.request(f"config.explain {path}")
        return game.run_ok("eval", f"{{config.explain {path}}}").stdout

    @mcp.tool()
    def baker_propose(text: str) -> str:
        """Replace the agent layer, data/agent.dta, with `text`, and keep it only if
        `check` passes. Otherwise the old file is restored. Returns
        {"kept": bool, "check": <baker.check/1>}."""
        target = game.own_path(str(AGENT_LAYER))
        old = target.read_bytes() if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".dta.proposed")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)
        try:
            p = game.run_ok("check", ok=(0, 1))
        except BaseException:
            restore(target, old)
            raise
        kept = p.returncode == 0
        if not kept:
            restore(target, old)
        return wrap(kept=kept, check=Raw(p.stdout))

    @mcp.tool()
    def baker_run(scenario: str | None = None, seeds: str | None = None, before: str | None = None) -> str:
        """Run scenarios headless: `sim [--scenario NAME] [--seeds A-B] --out DIR`.

        `seeds` is a range like "1-20". Each run goes to its own directory under runs/,
        named in the result as "out". Pass a previous run's "out" as `before` to get
        `diff` between that run and this one. "exit": 0 all objectives passed, 1 one
        failed, 2 the run could not run."""
        out = game.own_path("runs", stamp())
        args = ["sim"]
        if scenario:
            args += ["--scenario", scenario]
        if seeds:
            if not all(part.isdigit() for part in seeds.split("-", 1)):
                raise ToolError(f"seeds is a range like 1-20, not {seeds!r}")
            args += ["--seeds", seeds]
        p = game.run(*args, "--out", str(out), timeout=game.sim_timeout)
        meaning = {0: "passed", 1: "failed", 2: "could not run"}.get(p.returncode, "unknown")
        compared = None
        if before and p.returncode in (0, 1):
            prev = game.own_path(before)
            compared = Raw(game.run_ok("diff", str(prev), str(out), ok=(0, 1)).stdout)
        rel = str(out.relative_to(game.directory.resolve()))
        return wrap(exit=p.returncode, result=meaning, out=rel, sim=Raw(p.stdout or p.stderr), diff=compared)

    @mcp.tool()
    def baker_ab(action: str, name: str | None = None) -> str:
        """A/B in the running game. `action` is "toggle" (switch the agent layer on or
        off), "snapshot" (save the state as `name`) or "restore" (return to `name`).
        Returns baker.reply/1."""
        if action == "toggle":
            return game.request("config.toggle agent")
        if action in ("snapshot", "restore"):
            if not name or not name.replace("_", "").replace("-", "").isalnum():
                raise ToolError(f"{action} needs a name of letters, digits, - and _")
            return game.request(f"config.{action} {name}")
        raise ToolError(f"action is toggle, snapshot or restore, not {action!r}")

    @mcp.tool()
    def baker_session() -> str:
        """The running game's session: {"journal", "unsaved", "loop"}, each the
        baker.reply/1 of `config.journal`, `config.unsaved` and `config.loop`."""
        return wrap(**{k: Raw(game.request(f"config.{k}")) for k in ("journal", "unsaved", "loop")})

    @mcp.tool()
    def baker_promote_preview() -> str:
        """What promoting the agent layer would change, from `promote` without --write.
        Writes it to patches/ for a person to review and apply; never applies it.
        Returns {"patch": path, "change": text}."""
        p = game.run_ok("promote")
        out = game.own_path("patches", f"promote-{stamp()}.patch")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(p.stdout, encoding="utf-8")
        return wrap(patch=str(out.relative_to(game.directory.resolve())), change=p.stdout)

    @mcp.resource("baker://vocabulary", mime_type="application/json", description="reference --json")
    def vocabulary() -> str:
        return game.run_ok("reference", "--json").stdout

    @mcp.resource("baker://skill", mime_type="text/markdown", description="The stack's agent skill")
    def skill() -> str:
        if game.skill is None or not game.skill.exists():
            return "No agent skill configured (start the server with --skill PATH)."
        return game.skill.read_text(encoding="utf-8")

    return mcp


def restore(target: Path, old: bytes | None) -> None:
    if old is None:
        target.unlink(missing_ok=True)
    else:
        tmp = target.with_suffix(".dta.restore")
        tmp.write_bytes(old)
        os.replace(tmp, target)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="baker-mcp", description=__doc__.splitlines()[0])
    ap.add_argument("--game", required=True, type=Path, help="the game's binary")
    ap.add_argument("--dir", type=Path, default=Path.cwd(), help="the directory the game runs from")
    ap.add_argument("--port", type=int, help="the running game's console port, on 127.0.0.1")
    ap.add_argument("--skill", type=Path, help="the stack's agent skill text")
    a = ap.parse_args(argv)
    game = Game(binary=a.game.resolve(), directory=a.dir.resolve(), port=a.port,
                skill=a.skill.resolve() if a.skill else None)
    build(game).run("stdio")


if __name__ == "__main__":
    main()
