# Spike 002: prove the minimal LIZA repair loop

- **Question from:** [`docs/backlog/20-liza-loop-spike.md`](../backlog/20-liza-loop-spike.md)
- **Date:** 2026-09-03
- **Status:** planned
- **Goal:** determine whether the minimal LIZA loop is capable of fixing a small Python module from a failing test before expanding scope.

## Hypothesis

The smallest viable LIZA agent can complete one narrow task class reliably: edit a small Python function or module so that a failing `pytest` file passes, using a minimal tool loop and a single working directory.

The project should not broaden until that loop is proven. The relevant question is not whether the agent can write code in the abstract; it is whether it can keep a coherent repair loop on the narrow task class this repository has defined.

## Scope fence

This spike is intentionally scoped to a very small set of constraints:

- one task class only
- one repo and one working directory
- no web access
- no bash tool
- no broad agent framework
- no persona compile step
- no multi-file app scaffolding
- no product polish

This is a deliberate act of scope control. The repository already contains the design rationale for why the first version must be narrow.

## Baseline architecture to test

The initial target is the v0 architecture already described in the ADRs and backlog items:

- Python 3.10+, managed by `uv`
- OpenAI-compatible provider client
- native + text tool protocols
- four tools: `read_file`, `write_file`, `list_dir`, `run_tests`
- JSONL transcript output for every request, response, tool call and tool result

The protocol default should be chosen by evidence. If native tool calling is stable enough, it becomes the primary mechanism; if not, the text protocol remains the fallback. The spike should answer that question empirically, not by preference.

## Experimental design

1. Create 5–10 short intro-level repair tasks.
2. Each task is a failing `pytest` suite for a single function or small module.
3. Run each task across a small number of model/protocol combinations.
4. Record:
   - pass/fail
   - tool-call validity
   - iteration count
   - wall time
   - transcript artifact
   - whether the model recovers from malformed or invalid tool arguments
5. Keep the tasks narrow enough that a single local model should be able to complete them without a broad scaffolding loop.

## What counts as evidence

A successful spike is not simply "the model wrote something plausible." It is a recorded end-to-end repair cycle that:

- receives the failing task
- inspects files
- calls tools intentionally
- reads the failing test output
- writes a fix
- reruns the test suite
- completes without human intervention

That is the actual definition of success for this project.

## Success criteria

The spike is complete when the project can say all of the following with evidence:

- LIZA can complete a full repair loop on a narrow task class.
- The transcript is replayable and useful for debugging.
- The unit suite passes without a running model server.
- The default tool protocol is grounded in observed behaviour rather than assumption.

## Non-goals for this spike

- self-improving personas
- multi-file app generation
- shell execution
- performance tuning for production systems
- dashboards, analytics or product polish
- anything that would require the project to broaden before the repair loop is proven

## Exit condition

This spike ends in one of two states:

1. The minimal repair loop is good enough to lock architecture and proceed to M2.
2. The loop fails in a way we can explain, and we know what to test next.

In either case, the repository gains a concrete record of the actual capability boundary instead of a vague aspiration.

## Planned development sequence after the spike

### M1: local model communication

- provider client and configuration
- transcript persistence
- openai-compatible request path
- stub inference server for deterministic tests

### M2: repair loop

- failed test → file read → patch → rerun cycle
- minimal tool system
- repeated passes until pass/fail is resolved

### M3: eval harness

- task directory and scoring runner
- model/protocol comparisons
- pass/fail and iteration metrics

### M4: growth velocity

- self-correction metric on iteration sequences
- comparison with the baseline, including whether the metric adds informational value beyond raw pass/fail

### Beyond M4

Only broaden the system if the transcript evidence says the narrow loop is stable. That means shell access, multi-file project support, and personas are all deferred until the core coding loop is demonstrably solid.
