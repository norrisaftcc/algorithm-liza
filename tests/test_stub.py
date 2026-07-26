"""Tests for the stub inference server.

These verify the *stub*, not LIZA — there is no agent loop yet. The point is
that every fixture in `tests/fixtures/` behaves the way its note claims, so
that later tests of the real loop can trust what they are replaying. A stub
that lies is worse than no stub.
"""

from __future__ import annotations

import json

import httpx
import pytest

from liza.stub import FIXTURE_SCHEMA, Fixture, FixtureError, StubServer

COMPLETIONS = "/chat/completions"


def post(client: httpx.Client, server: StubServer, **body) -> httpx.Response:
    return client.post(server.base_url + COMPLETIONS, json=body or {"messages": []})


def message(response: httpx.Response) -> dict:
    return response.json()["choices"][0]["message"]


# --------------------------------------------------------------------------
# Fixture loading
# --------------------------------------------------------------------------


def test_every_fixture_in_the_repo_loads(fixture_dir):
    """A malformed fixture must fail loudly at load time, not mid-test."""
    paths = sorted(fixture_dir.glob("*.jsonl"))
    assert paths, "no fixtures found — the suite would pass vacuously"
    for path in paths:
        loaded = Fixture.from_path(path)
        assert loaded.name
        assert loaded.note, f"{path.name} has no note explaining what it exercises"


def test_fixture_provenance_is_declared(fixture_dir):
    """`observed` distinguishes a recorded transcript from one we made up.

    All fixtures are invented at M1 because no real model has been run yet.
    When that changes this test should start failing, which is the intent — it
    is a reminder to promote real transcripts rather than an assertion that
    inventing them is correct.
    """
    for path in sorted(fixture_dir.glob("*.jsonl")):
        assert Fixture.from_path(path).observed is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", "empty"),
        ('{"schema": "wrong/9"}', "header"),
        (f'{{"schema": "{FIXTURE_SCHEMA}"}}\nnot json', "not valid JSON"),
        (
            f'{{"schema": "{FIXTURE_SCHEMA}"}}\n{{"assistant": {{}}, "http": {{}}}}',
            "exactly one",
        ),
        (f'{{"schema": "{FIXTURE_SCHEMA}"}}\n{{"nonsense": 1}}', "exactly one"),
        (f'{{"schema": "{FIXTURE_SCHEMA}", "on_exhaustion": "shrug"}}', "on_exhaustion"),
        (f'{{"schema": "{FIXTURE_SCHEMA}", "on_exhaustion": "repeat_last"}}', "at least one"),
    ],
)
def test_malformed_fixtures_are_rejected(text, expected):
    with pytest.raises(FixtureError, match=expected):
        Fixture.from_text(text)


# --------------------------------------------------------------------------
# The baseline
# --------------------------------------------------------------------------


def test_happy_path_is_tool_call_then_answer(stub, client):
    server = stub("happy_path")

    first = post(client, server, messages=[{"role": "user", "content": "what does hello.py do?"}])
    assert first.json()["choices"][0]["finish_reason"] == "tool_calls"
    call = message(first)["tool_calls"][0]["function"]
    assert call["name"] == "read_file"
    assert json.loads(call["arguments"]) == {"path": "hello.py"}

    second = post(client, server)
    assert second.json()["choices"][0]["finish_reason"] == "stop"
    assert "greeting" in message(second)["content"]


def test_requests_are_recorded_for_assertions(stub, client):
    server = stub("happy_path")
    post(client, server, messages=[{"role": "user", "content": "hi"}], temperature=0.0)

    assert len(server.requests) == 1
    assert server.requests[0].body["messages"][0]["content"] == "hi"
    assert server.requests[0].body["temperature"] == 0.0


def test_usage_is_reported_so_token_accounting_can_be_tested(stub, client):
    server = stub("happy_path")
    assert post(client, server).json()["usage"]["prompt_tokens"] == 812


# --------------------------------------------------------------------------
# The failure modes that justify the stub existing
# --------------------------------------------------------------------------


def test_malformed_tool_args_are_served_verbatim(stub, client):
    """The stub must not repair the model's bad JSON on its way through."""
    server = stub("malformed_tool_args")
    raw = message(post(client, server))["tool_calls"][0]["function"]["arguments"]

    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)

    # The second turn is well-formed: the fixture models recovery, not just failure.
    recovered = message(post(client, server))["tool_calls"][0]["function"]["arguments"]
    assert json.loads(recovered) == {"path": "hello.py"}


def test_unknown_tool_is_a_tool_the_harness_does_not_implement(stub, client):
    server = stub("unknown_tool")
    assert message(post(client, server))["tool_calls"][0]["function"]["name"] == "bash"


def test_repeated_tool_call_is_identical_across_turns(stub, client):
    server = stub("repeated_tool_call")
    calls = [message(post(client, server))["tool_calls"][0]["function"] for _ in range(3)]

    assert len({c["name"] for c in calls}) == 1
    assert len({c["arguments"] for c in calls}) == 1
    # It does terminate, which is what separates this from a runaway.
    assert message(post(client, server)).get("content")


def test_runaway_never_stops(stub, client):
    """Only a step ceiling in the harness ends this. There is no natural end."""
    server = stub("runaway")
    for _ in range(20):
        assert message(post(client, server)).get("tool_calls"), "runaway should never answer"
    assert server.turns == 20


def test_prose_instead_of_tool_call_looks_like_a_final_answer(stub, client):
    """Under the native protocol this is indistinguishable from an answer.

    That indistinguishability is the whole argument for ADR-0002's second tool
    protocol, so it is asserted here rather than left implicit.
    """
    server = stub("prose_instead_of_tool_call")
    reply = message(post(client, server))

    assert "tool_calls" not in reply
    assert "read_file" in reply["content"]


def test_truncated_body_is_not_valid_json(stub, client):
    server = stub("truncated_body")
    response = post(client, server)

    assert response.status_code == 200
    with pytest.raises(json.JSONDecodeError):
        response.json()


def test_server_error_is_passed_through(stub, client):
    server = stub("server_error")
    response = post(client, server)

    assert response.status_code == 500
    assert "KV cache" in response.text


def test_slow_first_token_delays_the_response(stub, client):
    server = stub("slow_first_token")
    with (
        httpx.Client(trust_env=False, timeout=0.05) as impatient,
        pytest.raises(httpx.ReadTimeout),
    ):
        post(impatient, server)

    # The same request succeeds with a timeout sized for local inference. It
    # gets the same entry again because the fixture repeats: a timed-out
    # request still consumed its turn server-side, and "the machine is slow,
    # always" is the condition being modelled anyway.
    assert message(post(client, server))["content"]


# --------------------------------------------------------------------------
# Exhaustion, routing, and other stub mechanics
# --------------------------------------------------------------------------


def test_exhausted_fixture_returns_409_naming_the_fixture(stub, client):
    """Overrunning a script is nearly always a bug in the test. Make it loud."""
    server = stub("happy_path")
    for _ in range(2):
        post(client, server)

    overrun = post(client, server)
    assert overrun.status_code == 409
    assert "happy-path" in overrun.json()["error"]["message"]


def test_repeat_last_serves_the_final_entry_forever(stub, client):
    server = stub("runaway")
    first = message(post(client, server))
    for _ in range(5):
        assert message(post(client, server)) == first


def test_model_list_probe_is_answered(stub, client):
    """Clients often list models before their first completion."""
    server = stub("happy_path")
    response = client.get(server.base_url + "/models")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "stub"


def test_unknown_route_is_404_not_a_hang(stub, client):
    server = stub("happy_path")
    assert client.post(server.base_url + "/embeddings", json={}).status_code == 404


def test_each_server_gets_its_own_port(stub):
    """Ephemeral ports keep parallel tests from colliding on a fixed one."""
    assert stub("happy_path").port != stub("runaway").port


def test_base_url_includes_the_v1_prefix(stub):
    assert stub("happy_path").base_url.endswith("/v1")
