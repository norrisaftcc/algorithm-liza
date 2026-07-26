# ADR-0003: Adopt SHODANN growth metrics — on LIZA's output, not on our commits

- **Status:** Proposed
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc

## Context

`algorithm-shodann` is a sibling project: a GitHub Actions bot that reviews
student pull requests and scores **growth velocity** — the delta between
submissions rather than the absolute quality of any one of them. Its
`src/shodann/velocity.py` is the authoritative implementation. It consumes a
`CodeMetrics` record (`coverage`, `test_count`, `complexity`, `loc`,
`functions`, `docstrings`, `lint_issues`, `syntax_errors`), diffs it against
the previous submission, and produces a composite score plus growth-positive
prose. Two guards are deliberate: simplifying code is never penalised, and lint
deltas only count when positive.

The open question for this project is whether those metrics are useful to us.
The honest answer is that there are two candidate applications and they are not
equally good.

**Applying SHODANN to our own pull requests** is the obvious reading and the
weaker one. SHODANN measures a *citizen* against their own past, on a
per-author ledger, and is tuned so that going from nothing to something scores
highly. On a greenfield repository with one or two authors, every early metric
is a delta from zero, so the scores will be large, flattering and
uninformative. It would also make us both the instrument and the subject, which
is a poor position from which to evaluate the instrument. There is a real but
modest benefit — a coverage-and-lint trend line on every PR, and dogfooding
that surfaces SHODANN's own bugs — and no serious cost, as long as nobody
mistakes the number for a measure of whether the project is going well.

**Applying SHODANN to the code LIZA generates** is the interesting one, and it
is a genuinely good fit. LIZA's target task class is intro-Python coursework;
SHODANN's target artefact is intro-Python coursework. The eval harness already
has to run `pytest` and collect coverage over LIZA's output, which is most of
`CodeMetrics` already. That gives us a single comparable number per
(model, prompt, protocol, task) tuple, and a *delta* across LIZA's own
iterations within a single task — which is exactly the thing that is otherwise
hard to see. "Did the model improve its own code after seeing the test
failure?" is the central question about a small-model coding agent, and it is a
growth-velocity question by construction.

## Decision

Adopt `shodann.velocity` as a **library**, applied to LIZA's eval output.

1. The eval harness emits a `CodeMetrics`-shaped JSON record per task
   iteration, using SHODANN's field names exactly. This costs nothing and is
   worth doing even if the rest of this ADR is later reversed.
2. Score each task's iteration sequence with `composite_score` to produce a
   self-correction score: does LIZA's code improve between attempt *n* and
   attempt *n+1*, and by how much.
3. Aggregate per model and per prompt version, so a model or prompt change
   produces a visible movement rather than an anecdote.
4. Depend on `algorithm-shodann` at a pinned commit. Do not copy
   `velocity.py`; a fork would silently diverge from the sibling project, and
   keeping one authoritative scoring implementation is most of the value.

Running SHODANN as a PR bot on this repository is deferred, not rejected — see
the backlog. It is cheap, and dogfooding will find SHODANN bugs, but it must
be introduced with the caveat above written down next to it.

## Consequences

- The eval harness inherits a schema constraint from a sibling project, and a
  breaking change there breaks us. The pinned commit contains the blast radius.
- We get one number that summarises a run, which is dangerous in the ordinary
  way that one number always is. Transcripts remain the primary artefact; the
  score is an index into them, not a replacement.
- Coverage and complexity extraction has to work on generated code that may not
  parse. `syntax_errors` is already a `CodeMetrics` field, so the failure mode
  is representable rather than fatal — a run that produces broken code scores
  badly instead of crashing the harness.
- If SHODANN's weighting turns out to be wrong for machine-generated code —
  plausible, since it was tuned for humans learning — we tune a local
  `VelocityConfig` rather than editing the shared maths. `velocity.tune()`
  exists for this.
