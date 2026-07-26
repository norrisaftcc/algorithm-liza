# ADR-0002: LIZA v0 architecture

- **Status:** Proposed
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc

## Context

LIZA is meant to be a code assistant driven by a *local* model, aimed at a
narrow class of task: write or repair a single small Python program or module,
of the kind assigned in an introductory or intermediate course. The stated
definition of done for the early project is that LIZA can be used as a simple
code assistant against a local model.

Two facts shape the design.

The first is that small models are not small versions of frontier models; they
are a different component with different failure modes. They lose the thread
over long contexts, they emit malformed JSON, they loop, and they degrade
sharply as the system prompt grows. The `little-coder` project's central claim
— that scaffold-model fit matters more than model size, and that a ~1000-token
system prompt with a ~7k cold-start context is what makes a 9.7B model
competitive — is the most useful prior art we have, and it argues against
building anything elaborate.

The second is that the previous four attempts failed. We do not have their
post-mortems, but the common shape of this failure is well known: a general
"build me a system" agent, an ambitious tool surface, and a framework
dependency that changes underneath the project. The scope discipline below is a
direct response.

## Decision

**Own the loop; do not fork `little-coder`.** `little-coder` is Node/TypeScript,
built on `pi`, and is roughly thirty extensions and thirty skill files deep. It
is excellent and we should use it — as an installed *baseline to benchmark
against*, not as a codebase to inherit. LIZA's agent loop must be small enough
for a student to read in an afternoon, because being readable is part of what
the project is for.

**Python 3.10+, managed by `uv`. No agent framework.** Dependencies are
`httpx`, `pydantic`, `pytest`, and `ruff`. No LangChain, no LlamaIndex, no
CrewAI. Framework churn is a plausible cause of at least one prior failure, and
the entire agent loop is under 300 lines without one. The 3.10 floor is set by
[ADR-0005](0005-development-environment.md): nothing here needs 3.11, and
matching the version the development sandbox can execute means the tests we run
are the tests that run.

**Talk to an OpenAI-compatible `/v1/chat/completions` endpoint over a
configurable base URL.** Named provider presets for LM Studio
(`127.0.0.1:1234`), Ollama (`127.0.0.1:11434`) and llama.cpp
(`127.0.0.1:8888`), each overridable by environment variable. This buys
provider portability for free and lets us swap in a cloud model to isolate
whether a failure is ours or the model's — which is the single most valuable
debugging move available to this project.

**The tool protocol is pluggable, with two implementations from day one.**
`native` uses OpenAI-style `tool_calls`; `text` parses fenced blocks out of
ordinary prose. Gemma-family models served through LM Studio have inconsistent
native tool-call support, and a harness that only speaks one protocol will be
mis-blamed for a model's serialisation failure. Which protocol a model needs is
an empirical question, so both must exist before we can answer it.

**Four tools in v0: `read_file`, `write_file`, `list_dir`, `run_tests`.** No
shell. A shell is the most useful tool and also the one that turns a confused
small model into a destructive one, and every additional tool costs system
prompt tokens that small models can least afford. `run_tests` runs `pytest`
against a fixed path, which is narrow enough to be safe and is the only
execution feedback the target task class actually needs. Shell access is
revisited in a later ADR, if at all.

**Every run writes a JSONL transcript to `.liza/runs/<run-id>.jsonl`.** Every
request, response, tool call and tool result. This is not a logging nicety; it
is the substrate for three other things — debugging, the metrics in
[ADR-0003](0003-adopt-shodann-growth-metrics.md), and deterministic tests.

**Unit tests replay recorded transcripts and never call a model.** The suite
must pass on a machine with no inference server, in CI, in seconds. Anything
that genuinely depends on model behaviour is not a unit test; it is an eval
task with a recorded score, per `CONTRIBUTING.md`.

**Scope fence for v0.** LIZA operates on one working directory, on tasks
phrased as "write/fix this function, module, or small program". It does not
scaffold applications, does not manage multi-file projects, and does not browse
the web. `README.md` already argues this narrowing is the right fit; this ADR
makes it a constraint rather than an intention.

## Alternatives considered

**Fork or vendor `little-coder`.** Fastest path to a working agent, and it is
already tuned for exactly our model class. Rejected as the primary path because
inheriting a Node toolchain and thirty extensions leaves us maintaining
someone else's abstractions while learning nothing about the loop — and
"understanding the loop" is a stated goal. It stays in the plan as the
comparison baseline, which is the role it serves best.

**Native tool-calling only.** Simpler, and correct for the models that support
it well. Rejected because it makes an untested assumption about Gemma-class
models the exact moment we most need to distinguish harness bugs from model
limits.

**Include a `bash` tool in v0.** Rejected on the safety and token-budget
grounds above; revisit once we have transcripts showing what the model actually
tries to reach for.

## Consequences

- We write our own loop, so loop bugs are ours. The replay-test design exists
  to make that tolerable.
- Two tool protocols is genuinely more code than one, and one of them will
  eventually be deleted once we know which. That deletion is a success
  condition, not waste.
- Refusing shell access will block some tasks. When it does, the transcript
  will say so, and that is the evidence a later ADR needs.
- Benchmarking against `little-coder` may show it is simply better. That is an
  acceptable and informative outcome; it is not a reason to have skipped
  building ours.
