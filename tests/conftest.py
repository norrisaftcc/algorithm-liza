"""Shared test fixtures.

Nothing in this suite calls a model or reaches the network beyond loopback.
That is a constraint worth defending: it is what lets the suite run on a CI
runner with no GPU, and it is what forces model-dependent behaviour into the
eval harness where it can be scored rather than asserted.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest

from liza.stub import StubServer

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def stub() -> Iterator[Callable[[str], StubServer]]:
    """Start a stub server from a fixture name, and stop it afterwards.

        def test_something(stub):
            server = stub("happy_path")
            ...
    """
    started: list[StubServer] = []

    def _start(name: str) -> StubServer:
        server = StubServer.from_path(FIXTURE_DIR / f"{name}.jsonl").start()
        started.append(server)
        return server

    yield _start

    for server in started:
        server.stop()


@pytest.fixture
def client() -> Iterator[httpx.Client]:
    """An httpx client configured the way LIZA's provider client must be.

    ``trust_env=False`` is the load-bearing part. With ``ALL_PROXY`` or
    ``HTTPS_PROXY`` set in the environment, httpx routes even loopback requests
    through the proxy, and the resulting failure reads as "the inference server
    isn't responding" rather than as a proxy problem. This was not a
    hypothetical — it broke the first stub run on a machine with a SOCKS proxy
    exported. See docs/adr/0005-development-environment.md.
    """
    with httpx.Client(trust_env=False, timeout=10.0) as c:
        yield c
