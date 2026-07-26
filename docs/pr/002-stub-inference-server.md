Closes ISSUE_18

<!-- seed-issues.sh prints the issue numbers it creates; open-prs.sh substitutes
     the one for docs/backlog/18-stub-inference-server.md into this line. -->

## What changed

First code in the repository. `src/liza/stub.py` speaks enough of the OpenAI
`/v1/chat/completions` shape that a provider client cannot tell it apart from LM
Studio, Ollama or llama.cpp, and replays a scripted sequence of responses read
from a JSONL fixture.

- `Fixture` / `FixtureError` — loads and validates a fixture, failing loudly at
  load time rather than mid-request.
- `StubServer` — serves one fixture over loopback on an ephemeral port, records
  every request for tests to assert against, and is a context manager.
- `liza-stub <fixture> --port` — the same server standalone, for pointing a real
  client at by hand.
- Nine fixtures in `tests/fixtures/`, and 26 tests.

An entry is one of `{"assistant": {...}}`, `{"raw_body": "..."}` or
`{"http": {"status": N, "body": "..."}}`, optionally with `delay_seconds`. The
three kinds exist because not every failure is expressible as a well-formed
completion: a truncated body is not JSON by definition, and a 500 has no
completion in it at all.

## Why this shape

The obvious reading is "we couldn't reach a GPU", and that is true but it is the
less interesting half. The responses this harness most needs to survive —
malformed tool-call arguments, a body that stops mid-JSON, the same tool call
repeated until the context fills, a run that never terminates — are ones a real
small model emits *occasionally and unpredictably*. Waiting for Gemma to
misbehave on cue is not a test strategy. This replays each of them identically
on every CI run, including on a runner with no GPU. See ADR-0005.

The corresponding risk is stated rather than hidden. A stub encodes our beliefs
about how models behave, and some of those beliefs are wrong. Every fixture
therefore carries an `observed` flag, and every fixture currently sets it to
`false`. `test_fixture_provenance_is_declared` asserts that they all are, which
means **that test is designed to fail** once real transcripts get promoted into
fixtures. That is a reminder, not an oversight.

The single most important fixture is `prose_instead_of_tool_call`, where the
model narrates the call it means to make instead of emitting one. Under the
native protocol that is indistinguishable from a final answer, and that
indistinguishability is the entire argument for the second, text-based tool
protocol in ADR-0002. It is asserted here rather than left as an assumption.

## How this was verified

`ruff check` clean, `pytest -q` green at 26 tests, both from a fresh clone of
this branch into a clean virtualenv. The `liza-stub` CLI was additionally
smoke-tested against a real `httpx` client outside the test suite, to confirm
the tests are not passing against something only the tests can talk to.

Two real bugs surfaced during that verification and are fixed here:

- **httpx honours `ALL_PROXY` / `HTTPS_PROXY` for loopback requests too.** On a
  machine with a system proxy exported, the first stub run failed with
  `Using SOCKS proxy, but the 'socksio' package is not installed` — and the
  general form of this presents to a user as "LM Studio isn't responding", not as
  a proxy problem. `tests/conftest.py` sets `trust_env=False` and backlog #03
  carries the requirement forward to the real provider client.
- **A request that times out client-side has still consumed its turn
  server-side.** The retry was landing on the exhaustion path and getting a 409.
  `slow_first_token` now sets `on_exhaustion: repeat_last`, which is also the
  more honest model of the situation — a slow machine is slow on the retry too.
  Relatedly, `_send_raw` now swallows `BrokenPipeError`, because a client hanging
  up mid-write is an event this stub deliberately provokes and should not
  produce a traceback for.

## Definition of done

- [x] Behaviour is covered by a test, or by an eval task if it is model-dependent
- [x] `ruff check` and `pytest` pass
- [x] Reasoning is captured in a docstring, an ADR, or this PR body
- [x] The linked issue's stated outcome is demonstrably true

## What this does not do

It does not prove LIZA works. Nothing here has spoken to a model. A harness that
passes every test in this PR can still fall over on first contact with Gemma,
and finding that out is what backlog #03 and #04 are for.
