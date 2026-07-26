# ADR-0005: Two machines — where LIZA is built and where LIZA is verified

- **Status:** Proposed
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc

## Context

Development on this project happens across two machines that cannot reach each
other, and the boundary was not obvious until it was tested.

The **Mac** holds the repository, the GitHub credentials, the inference servers,
and the RAM to run a model. The **agent sandbox** is a 4-core, 3 GB aarch64
Linux container with `uv`, Python, Node and git, network egress restricted to
an allowlist (PyPI, npm, github.com, Ubuntu archives), and a read-write mount of
the repository directory.

What was measured, rather than assumed:

- Every route from the sandbox to a Mac-hosted inference server —
  `127.0.0.1`, `host.docker.internal`, `host.lima.internal`, the gateway
  address — is refused by the network allowlist. Installing Ollama on the Mac
  does not make it reachable from the sandbox. Nothing about the sandbox's
  configuration is likely to change this.
- The sandbox cannot host a model either. 3 GB of RAM rules it out on its own,
  and model weights live on hosts that are not allowlisted.
- The sandbox cannot push to GitHub: no credentials, no `gh`. It can clone and
  fetch public repositories, which is how the sibling projects were surveyed.
- `uv` cannot download a managed CPython in the sandbox — the release assets
  redirect to a host outside the allowlist — so the sandbox is pinned to its
  system Python 3.10. `httpx`, `pydantic`, `pytest` and `ruff` all install and
  run there without difficulty.
- The sandbox exports `ALL_PROXY` pointing at a SOCKS proxy, and `httpx` honours
  it by default for *every* request including loopback. This is the environment
  reproducing, by accident, one of the more annoying real-world failures for a
  local-inference client.

The temptation is to treat this as a tooling problem to be solved before work
can start. It is not. Almost none of LIZA's code needs a real model to be
written or tested.

## Decision

**Split the work by what it actually depends on.** Harness code — the loop,
tool dispatch, transcript format, protocol parsing, error recovery — is
developed and tested in the sandbox. Only behaviour that genuinely depends on
model cognition is verified on the Mac.

**Build a fixture-driven stub inference server, and treat it as a deliverable
rather than a testing hack.** It is an OpenAI-compatible endpoint that replays
a scripted sequence of responses. A forty-line proof of concept already drives
a full tool-call cycle and a malformed-arguments recovery.

The argument for it is not merely that the sandbox lacks a model. It is that
the responses we most need to handle — malformed tool arguments, a truncated
JSON body, the same tool call repeated forever, a runaway that never stops —
are exactly the ones a real model produces *occasionally and unpredictably*.
Waiting for Gemma to misbehave on demand is a bad test strategy. Being able to
reproduce its worst behaviour deterministically, on every CI run, is worth more
than intermittent access to the real thing.

**Lower the Python floor to 3.10.** Nothing in the design needs 3.11, and
matching the version the sandbox can actually execute means the tests I run are
the tests that run. This amends
[ADR-0002](0002-liza-v0-architecture.md) before it merges.

**The provider client disables proxy environment discovery** (`trust_env=False`
in `httpx`, or an explicit no-proxy for loopback). Discovered here by accident,
but it is a genuine failure mode on any machine with a system or corporate
proxy configured, and it presents as "LM Studio isn't responding" rather than
as a proxy error.

**Mac-side execution is deferred and deliberately narrow if adopted.** The
capability that would actually change what I can do is not Ollama access — it
is the ability to run commands on the Mac at all, which would unblock
`git push`, `gh`, and above all the M2 spike's twenty-trial measurement.
Screen control is not a route to it: terminals and IDEs are restricted to
click-only, so shell commands cannot be typed. That leaves a locally installed
MCP server, which is real work with a real security surface, and if it is built
it should be scoped to running a named set of commands in this repository —
not a general shell. Filed in the backlog, not scheduled.

## Consequences

- Development is unblocked immediately, with no new tooling on the Mac. This is
  the main point of the ADR.
- **A stub encodes our beliefs about how models behave, and our beliefs will be
  wrong.** A harness that passes every stub test can still fail on first
  contact with Gemma. The mitigation is directional: transcripts recorded from
  real runs on the Mac are committed back as fixtures, so the stub's repertoire
  grows from observed reality rather than imagination. Any fixture that was
  never observed in a real transcript should say so in a comment.
- The Mac still needs `uv` for anyone to run the project there
  (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `brew install uv`),
  and an inference server for M2 onward. Those are the user's steps; the
  sandbox cannot perform them.
- Pushing branches and filing issues remains a manual step on the Mac until and
  unless the execution MCP exists.
- Pinning to Python 3.10 costs us `match` ergonomics and some typing niceties.
  Cheap, and it widens compatibility on student machines, which is a mild
  independent benefit given the target audience.
