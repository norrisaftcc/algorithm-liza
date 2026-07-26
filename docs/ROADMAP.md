# LIZA Roadmap

Five milestones. Each has a definition of done that can be checked by running
something, not by agreeing that it feels finished. Milestones are sequential;
the fence around each is there to stop the project from becoming the four
repositories that came before it.

## M0 — Project scaffolding *(this milestone)*

Establish the workflow, the decisions, and the persona bank before writing
agent code.

**Done when:** `CONTRIBUTING.md`, `docs/ROADMAP.md` and ADRs 0001–0004 are
merged to `main`; the backlog exists as real GitHub issues; issue and PR
templates are in place; the imported personas are versioned under `agents/`.

## M1 — LIZA talks to a local model

The smallest thing that is recognisably an agent: config, an OpenAI-compatible
client, one tool protocol, a transcript, and the stub inference server that
lets all of the above be tested without a model
([ADR-0005](adr/0005-development-environment.md)).

**Done when:** `liza --provider lmstudio "read hello.py and tell me what it
does"` completes a full request → tool call → tool result → answer cycle
against a locally served model, and writes a replayable JSONL transcript to
`.liza/runs/`. The unit suite passes with no inference server running.

**Explicitly not in M1:** the second tool protocol, the eval harness, personas.

## M2 — LIZA writes and repairs code

The four tools of [ADR-0002](adr/0002-liza-v0-architecture.md), the
edit-test-repair loop, and the `text` tool protocol alongside `native`.

**Done when:** given a natural-language spec and a failing `pytest` file, LIZA
writes a module, runs the tests, reads the failure, and revises — completing
at least one such cycle unaided against a local model. Both tool protocols run
the same task, and the transcripts of both are committed as fixtures.

**This is the project's stated early definition of done:** LIZA usable as a
simple code assistant on a local model. Everything after this is measurement.

## M3 — The eval harness

A `tasks/` directory of intro-Python problems, each a prompt plus a pytest
file, and a runner that scores LIZA across models, protocols and prompt
versions.

**Done when:** `liza-eval --model <m> --protocol <p>` runs the full task suite
unattended and emits a JSON report containing, per task, pass/fail, iteration
count, wall time, token counts, and a SHODANN-shaped `CodeMetrics` record per
iteration. Ten tasks minimum, spanning trivially easy to reliably-fails, so the
suite has headroom in both directions.

## M4 — Growth velocity

Wire [ADR-0003](adr/0003-adopt-shodann-growth-metrics.md) up: score the
iteration sequences, aggregate, and answer the question the project actually
asked.

**Done when:** an eval report carries a per-task self-correction velocity score
and a per-model aggregate; a written comparison of at least two local models
exists in `docs/`; and `little-coder` has been run on the same task suite as a
baseline. The comparison must state plainly whether the velocity metric told us
anything the raw pass/fail did not — including if the answer is no.

## Fenced off, deliberately

Not scheduled, not forgotten. Each needs an ADR before it starts.

- A `bash` tool ([ADR-0002](adr/0002-liza-v0-architecture.md) argues against it
  for v0; the M2 transcripts are the evidence for revisiting).
- Multi-file project scaffolding, the task class the previous four attempts
  died on.
- SHODANN as a PR bot on this repository.
- Compact persona variants for LIZA, and the persona compile step
  ([ADR-0004](adr/0004-persona-and-skill-bank.md)).
- Mining the four earlier repositories for ideas. LIZA gets to do this herself
  once she works — it is a good first real task and a bad first dependency.
