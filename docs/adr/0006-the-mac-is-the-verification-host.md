# ADR-0006: The Mac is the verification host

- **Status:** Accepted
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc
- **Amends:** [ADR-0005](0005-development-environment.md)

## Context

[ADR-0005](0005-development-environment.md) records a set of environment facts —
no route to an inference server, no GitHub credentials, no `gh`, no `uv`-managed
CPython, an `ALL_PROXY` that captures loopback — and states them as flat
assertions about "the environment". They were measured honestly and they are
correct. But they are properties of **the agent sandbox specifically**, and the
ADR does not say so. Read on the Mac, several of its sentences are simply false.

What is true on this machine, verified rather than assumed:

- `gh` is installed and authenticated. Issues and pull requests are readable and
  writable directly — PR #21 was reviewed and closed from an agent session on
  this machine, no manual step involved.
- `git push` works. Credentials are present.
- Ollama 0.32.4 is running and serves an OpenAI-compatible API at
  `127.0.0.1:11434/v1`, with `gemma4:e4b` and `gemma4:12b` both installed.
  [Spike 001](../spikes/001-gemma4-native-tool-calls.md) ran 45 real model calls
  against it.
- The test suite runs. `pytest` and `ruff` are available in a virtualenv.

The consequence ADR-0005 draws — *"Pushing branches and filing issues remains a
manual step on the Mac until and unless the execution MCP exists"* — is
therefore satisfied, but not in the way it anticipated. It is not that the
capability was built. It is that the capability was **already present on the
machine that has the models**, and the ADR's framing obscured that by attaching
sandbox limits to the project rather than to the sandbox.

This matters beyond bookkeeping. ADR-0005's central mitigation is that
"transcripts recorded from real runs on the Mac are committed back as fixtures",
which is the only defence against the stub encoding wrong beliefs. That loop is
much shorter than the ADR assumed.

## Decision

**ADR-0005's environment findings are scoped to the agent sandbox.** Every
measurement in it stands; none of it describes this Mac. Where ADR-0005 says
"the environment cannot X", read "the sandbox cannot X".

**The Mac is the verification host.** Anything that depends on model cognition —
spikes, eval tasks, transcript recording, the M2 tool-call measurements — runs
here, against Ollama, and its output is committed. Harness code remains
developable anywhere, which is the half of ADR-0005 that was always right and is
unaffected.

**An agent session on the Mac may drive `gh`, `git`, `ollama`, `pytest` and
`ruff` directly.** This is dev activity on a dev laptop by the machine's owner,
not a service exposed to anything. Treating it as a security boundary requiring
its own MCP was over-weighting the risk.

**Backlog item [19](../backlog/19-mac-side-execution.md) is closed as
unnecessary.** Its entire justification was that the sandbox cannot reach `gh`,
`git` or `ollama`, making the M2 spike a manual grind. Work done on the Mac
reaches all of them, so the justification is gone rather than merely weakened.
The item already floated "a reasonable answer is no"; this is that answer, on
evidence. The narrow-command-allowlist reasoning it contains should be preserved
if a *remote* execution surface is ever proposed — the irony it names, of
granting a general shell in order to build an agent ADR-0002 denies a shell to,
remains a good argument in that setting.

**`uv` stays the documented toolchain.** ADR-0002 specifies it and ADR-0005
notes the Mac needs it installed. That has not happened yet, so
`CONTRIBUTING.md`'s documented commands currently fail here. The fix is to
install `uv`, not to change the docs — but until it is installed, the docs
describe an environment that does not exist on the only machine that can run
the models.

## Alternatives considered

**Edit ADR-0005 in place to add "in the sandbox" qualifiers.** Rejected:
[ADR-0001](0001-record-architecture-decisions.md) forbids editing merged ADRs
except for the Status line, and the original measurements have standalone value
as a record of what a restricted environment actually permits.

**Build the Mac-side execution MCP anyway,** on the grounds that it would help a
future sandbox session. Rejected: it solves a problem that only exists when work
happens in the sandbox, and the work that needs a model cannot happen there by
definition. Build it if and when a remote agent genuinely needs to drive this
machine.

## Consequences

- The M2 spike is cheap to re-run rather than a manual grind, which is what made
  [Spike 001](../spikes/001-gemma4-native-tool-calls.md) possible at 45 model
  calls instead of a hand-counted twenty.
- Real transcripts can now be promoted into `tests/fixtures/` with
  `observed: true`. **This will fail `test_fixture_provenance_is_declared`,
  which asserts every fixture is invented — by design.** Its docstring says the
  failure "is a reminder to promote real transcripts rather than an assertion
  that inventing them is correct." That reminder is now due.
- Spike 001 found that none of the four invented failure-mode fixtures
  (`prose_instead_of_tool_call`, `malformed_tool_args`, `truncated_body`,
  `runaway`) occurred in 40 trials. They are hypotheses that have not yet been
  observed, and the fixture set currently over-represents serialisation failure
  relative to what these models actually do.
- Two machines still cannot reach each other, and nothing here changes that.
  Splitting work by what it depends on remains correct.
- Recording environment facts without naming the environment they were measured
  in is the error this ADR corrects. Future measurements should name the host.
