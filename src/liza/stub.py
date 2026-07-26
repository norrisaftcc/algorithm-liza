"""A fixture-driven stand-in for a local inference server.

Speaks enough of the OpenAI ``/v1/chat/completions`` shape that LIZA's provider
client cannot tell it apart from LM Studio, Ollama or llama.cpp, and replays a
scripted sequence of responses read from a JSONL fixture.

Why this exists is worth stating, because "we couldn't reach a GPU" is only
half of it and the less interesting half. The responses the harness most needs
to survive — malformed tool-call arguments, a body that stops mid-JSON, the
same tool call repeated until the context fills, a run that never terminates —
are ones a real small model emits *occasionally and unpredictably*. Waiting for
Gemma to misbehave on cue is not a test strategy. This replays each of them on
demand, identically, on every CI run.

The corresponding risk is that a stub encodes our beliefs about how models
behave, and some of those beliefs are wrong. Fixtures therefore carry an
``observed`` flag: ``true`` means the sequence was lifted from a real recorded
transcript, ``false`` means we invented it and it should be treated as a
hypothesis. See ``docs/adr/0005-development-environment.md``.

Run it standalone against a real client::

    liza-stub tests/fixtures/happy_path.jsonl --port 8899

Or drive it from a test::

    with StubServer.from_path("tests/fixtures/happy_path.jsonl") as stub:
        ...  # stub.base_url points at it; stub.requests records what arrived
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

__all__ = ["Fixture", "FixtureError", "StubServer", "FIXTURE_SCHEMA"]

FIXTURE_SCHEMA = "liza.fixture/1"

# Exactly one of these keys must appear in each entry; it selects what the stub
# does for that turn.
_ENTRY_KINDS = ("assistant", "raw_body", "http")


class FixtureError(ValueError):
    """A fixture file is malformed. Raised at load time, never mid-request."""


@dataclass
class Fixture:
    """One scripted conversation: a header line, then one entry per turn.

    The file is JSONL. The first line is the header::

        {"schema": "liza.fixture/1", "name": "happy-path", "observed": false}

    and every line after it is one response, consumed in order.

    ``on_exhaustion`` decides what happens when the harness asks for more turns
    than the script provides. The default is ``"error"``, which answers HTTP 409
    and makes the overrun loud, because a test that runs longer than its script
    is nearly always a bug in the test. The exception is a deliberate runaway,
    which sets ``"repeat_last"`` and hands back the same response forever.
    """

    name: str
    entries: list[dict[str, Any]]
    on_exhaustion: str = "error"
    observed: bool = False
    note: str = ""

    @classmethod
    def from_path(cls, path: str | Path) -> Fixture:
        path = Path(path)
        try:
            return cls.from_text(path.read_text(), source=str(path))
        except FixtureError as exc:
            raise FixtureError(f"{path}: {exc}") from None

    @classmethod
    def from_text(cls, text: str, source: str = "<string>") -> Fixture:
        lines = [ln for ln in (raw.strip() for raw in text.splitlines()) if ln]
        if not lines:
            raise FixtureError("file is empty")

        parsed: list[dict[str, Any]] = []
        for lineno, line in enumerate(lines, start=1):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FixtureError(f"line {lineno} is not valid JSON: {exc}") from None
            if not isinstance(obj, dict):
                raise FixtureError(f"line {lineno} is not a JSON object")
            parsed.append(obj)

        header, entries = parsed[0], parsed[1:]
        if header.get("schema") != FIXTURE_SCHEMA:
            raise FixtureError(
                f"first line must be a header with schema {FIXTURE_SCHEMA!r}, "
                f"got {header.get('schema')!r}"
            )

        on_exhaustion = header.get("on_exhaustion", "error")
        if on_exhaustion not in ("error", "repeat_last"):
            raise FixtureError(f"unknown on_exhaustion {on_exhaustion!r}")
        if not entries and on_exhaustion == "repeat_last":
            raise FixtureError("on_exhaustion 'repeat_last' needs at least one entry to repeat")

        for index, entry in enumerate(entries):
            kinds = [k for k in _ENTRY_KINDS if k in entry]
            if len(kinds) != 1:
                found = kinds or "none"
                raise FixtureError(
                    f"entry {index} must have exactly one of {_ENTRY_KINDS}, found {found}"
                )

        return cls(
            name=header.get("name", source),
            entries=entries,
            on_exhaustion=on_exhaustion,
            observed=bool(header.get("observed", False)),
            note=header.get("note", ""),
        )


@dataclass
class _Recorded:
    """One request as the stub received it, for tests to assert against."""

    path: str
    body: dict[str, Any]
    headers: dict[str, str]


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # The default handler logs every request to stderr, which buries pytest
    # output under noise that says nothing a failing assertion won't.
    def log_message(self, *args: Any) -> None:  # noqa: A002 - signature is fixed
        pass

    @property
    def _stub(self) -> StubServer:
        return self.server.stub  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        # LM Studio and Ollama clients often probe for a model list before
        # their first completion. Answering keeps that probe from looking like
        # a connection failure.
        if self.path.rstrip("/").endswith("/models"):
            self._send_json(200, {"object": "list", "data": [{"id": "stub", "object": "model"}]})
        else:
            self._send_json(404, {"error": {"message": f"no route for GET {self.path}"}})

    def do_POST(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""

        if not self.path.rstrip("/").endswith("/chat/completions"):
            self._send_json(404, {"error": {"message": f"no route for POST {self.path}"}})
            return

        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": {"message": "request body was not valid JSON"}})
            return

        self._stub._record(_Recorded(self.path, body, dict(self.headers)))

        entry = self._stub._next_entry()
        if entry is None:
            self._send_json(
                409,
                {
                    "error": {
                        "message": (
                            f"fixture {self._stub.fixture.name!r} is exhausted after "
                            f"{len(self._stub.fixture.entries)} turns. The harness asked for "
                            "another one, which usually means the loop failed to stop."
                        )
                    }
                },
            )
            return

        delay = entry.get("delay_seconds")
        if delay:
            time.sleep(float(delay))

        if "http" in entry:
            spec = entry["http"]
            self._send_raw(int(spec.get("status", 500)), str(spec.get("body", "")).encode())
        elif "raw_body" in entry:
            # Deliberately not serialised through json.dumps: this is how a
            # truncated or otherwise corrupt body gets expressed.
            self._send_raw(int(entry.get("status", 200)), str(entry["raw_body"]).encode())
        else:
            self._send_json(200, self._completion(entry))

    def _completion(self, entry: dict[str, Any]) -> dict[str, Any]:
        message = dict(entry["assistant"])
        message.setdefault("role", "assistant")
        finish = "tool_calls" if message.get("tool_calls") else "stop"
        return {
            "id": f"chatcmpl-stub-{self._stub.turns}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": entry.get("model", "stub"),
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": entry.get(
                "usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            ),
        }

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        self._send_raw(status, json.dumps(payload).encode(), "application/json")

    def _send_raw(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # A client that gave up waiting is an event this stub deliberately
            # provokes — see the slow_first_token fixture. Letting the write
            # error escape would print a traceback for a working test.
            pass


class StubServer:
    """Serves a :class:`Fixture` over loopback on an ephemeral port.

    Binding to port 0 rather than a fixed port is deliberate: tests run in
    parallel, and a hardcoded port turns that into an intermittent failure that
    looks like a bug in the harness.
    """

    def __init__(self, fixture: Fixture, host: str = "127.0.0.1", port: int = 0) -> None:
        self.fixture = fixture
        self.turns = 0
        self.requests: list[_Recorded] = []
        self._lock = threading.Lock()
        self._httpd = ThreadingHTTPServer((host, port), _Handler)
        self._httpd.daemon_threads = True  # a delayed response must not block shutdown
        self._httpd.stub = self  # type: ignore[attr-defined]
        self._thread: threading.Thread | None = None

    @classmethod
    def from_path(cls, path: str | Path, **kwargs: Any) -> StubServer:
        return cls(Fixture.from_path(path), **kwargs)

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def base_url(self) -> str:
        """The value to hand a provider client as its base URL, ``/v1`` included."""
        host, port = self._httpd.server_address[0], self.port
        return f"http://{host}:{port}/v1"

    def start(self) -> StubServer:
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> StubServer:
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    def _record(self, request: _Recorded) -> None:
        with self._lock:
            self.requests.append(request)

    def _next_entry(self) -> dict[str, Any] | None:
        """The response for this turn, or ``None`` when the script has run out."""
        with self._lock:
            index = self.turns
            self.turns += 1
            entries = self.fixture.entries
            if index < len(entries):
                return entries[index]
            if self.fixture.on_exhaustion == "repeat_last" and entries:
                return entries[-1]
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fixture", help="path to a JSONL fixture")
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)

    stub = StubServer.from_path(args.fixture, host=args.host, port=args.port)
    provenance = "observed in a real transcript" if stub.fixture.observed else "invented"
    print(f"fixture {stub.fixture.name!r} ({provenance}), {len(stub.fixture.entries)} turns")
    if stub.fixture.note:
        print(f"note: {stub.fixture.note}")
    print(f"serving {stub.base_url}  (ctrl-c to stop)")

    stub.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\nserved {len(stub.requests)} request(s)")
    finally:
        stub.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
