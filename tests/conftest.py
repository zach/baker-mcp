import asyncio
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from mcp.client import Client

from baker_mcp.server import Game, build


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(game, tool, **args):
    """Call a tool through an in-process MCP client; returns (is_error, text)."""

    async def go():
        async with Client(build(game)) as c:
            r = await c.call_tool(tool, args)
            return r.is_error, r.content[0].text

    return asyncio.run(go())


def call_json(game, tool, **args):
    err, text = call(game, tool, **args)
    assert not err, text
    return json.loads(text)


def read(game, uri):
    async def go():
        async with Client(build(game)) as c:
            return (await c.read_resource(uri)).contents[0].text

    return asyncio.run(go())


def start_console(argv, cwd, port):
    """Start a headless game with a console, and wait until the port accepts."""
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(300):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError(f"game exited {proc.returncode}")
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("console never opened")


@pytest.fixture
def fake(tmp_path):
    """A game directory and the stand-in binary."""
    (tmp_path / "data").mkdir()
    return Game(binary=Path(__file__).with_name("fakegame.py"), directory=tmp_path)


@pytest.fixture
def fake_live(fake):
    fake.port = free_port()
    proc = start_console([sys.executable, str(fake.binary), "--headless", "--console-port", str(fake.port)],
                         fake.directory, fake.port)
    yield fake
    proc.kill()
    proc.wait()
