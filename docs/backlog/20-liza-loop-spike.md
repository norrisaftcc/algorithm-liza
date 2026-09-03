---
title: "Spike: prove the minimal LIZA repair loop"
labels: ["type:spike", "milestone:M2", "area:core", "area:eval"]
---
Timeboxed to one week and intentionally narrow: a single task class, a single repo, one working directory, no web access, no bash tool, no broad agent framework, and no persona compile step.

The question is simple and testable: can a minimal local-model coding agent reliably repair a small Python function or module from a failing `pytest` run using an intentionally small tool loop?

This is the gate before broadening the project. If the loop cannot complete a narrow repair cycle without human intervention, the project should not add more breadth: no multi-file scaffolding, no additional shell access, no teaching persona layer, no analytics dashboard. The spike is meant to answer whether the project is ready to move from "LIZA talks to a model" into an actual edit-test-repair system.

## Candidate architecture to test

The current v0 design is the baseline, and it should be treated as a testable hypothesis until the spike proves otherwise:

- Python 3.10+, managed by `uv`
- OpenAI-compatible provider client, configurable by base URL
- Four tools only: `read_file`, `write_file`, `list_dir`, `run_tests`
- Native and text tool protocols, with the default determined by evidence on the actual model and host
- JSONL transcript written for every request, tool call and tool result
- One working directory and one task class only

This is intentionally small enough to read, debug and trust.

## What gets measured

Run a small suite of 5–10 intro-level Python repair tasks across a limited set of model/protocol combinations. Record:

- pass/fail
- tool-call validity
- iteration count to completion
- wall-clock time
- transcript artifact
- whether the model recovered after a bad tool call or malformed output

The metric is not whether the model produced polished prose. The metric is whether it could drive a complete cycle from failing test → read → patch → rerun → pass without a human steering the loop.

## Success criteria

The spike is successful when all of the following are true:

- the loop completes at least one end-to-end repair cycle unaided
- the transcript is replayable and useful for debugging
- the test suite passes with no model server running
- the default protocol is chosen by evidence, not by assumption

## Explicit non-goals

- self-improving personas
- large-project scaffolding
- multi-file app generation
- broad web or shell access
- product polish or UI work
- anything that cannot be justified by a recorded transcript or eval result

## Exit condition

The project either:

1. picks a protocol and locks the minimal architecture, or
2. learns exactly why the loop fails and what to test next.

Either outcome is valuable. A broad project without a proven minimal loop is a repeat of the previous failures.

---

## Future development plan

### M1: LIZA talks to a local model

- provider client and config
- transcript output
- tool protocol plumbing
- stub inference server so the unit suite does not depend on a model

Done when a real request completes a full request → tool call → tool result → answer cycle against a local model and writes a JSONL run to `.liza/runs/`.

### M2: LIZA writes and repairs code

- add the edit-test-repair loop
- validate on a small failing-Python task suite
- make the model revise based on pytest output without human intervention

Done when LIZA writes or repairs a small module in response to a failing `pytest` file and passes at least one full repair cycle unaided.

### M3: the eval harness

- add tasks/ with intro/intermediate Python problems and pytest fixtures
- add a runner that reports pass/fail, iteration count, wall time, and token counts
- score across models and tool protocols

Done when the harness runs unattended and emits a per-task evaluation report.

### M4: growth velocity

- integrate the SHODANN-style self-correction metric
- compare raw pass/fail with improvement-over-iterations
- compare against a baseline such as `little-coder`

Done when the project can state whether growth velocity tells us anything not already visible from pass/fail.

### Beyond M4

Expand only when the evidence justifies it:

- bash access only if repeated transcripts show it is required
- multi-file project work only after the single-file repair loop is stable
- personas and teaching workflows only after the coding loop is measurable and reliable

This is the discipline that keeps the project narrow enough to learn from.
