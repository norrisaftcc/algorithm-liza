# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc

## Context

Four earlier repositories attempted fragments of this project. None of them
work. More importantly, none of them explain *why* they were built the way they
were, so none of them can be salvaged by reading — only by re-deriving. The
code survived and the reasoning did not.

That asymmetry is the actual defect. Code rots quietly; a written decision with
its context attached stays useful even after the code it describes is deleted.

## Decision

Every decision that constrains future work is recorded as an ADR in
`docs/adr/`, numbered sequentially, in the format used by this file: Context,
Decision, Consequences, and where relevant Alternatives considered.

An ADR is warranted when a choice is expensive to reverse, when a reasonable
person would have chosen differently, or when a future reader would otherwise
ask "why on earth is it like this?". Routine implementation choices do not need
one.

ADRs are immutable once merged. Changing course means writing a new ADR whose
Status line names the one it supersedes, and editing only the Status line of
the old one to point forward.

Negative results are recorded with the same weight as positive ones. "We tried
X, here is the transcript, it did not work because Y" is the single most
valuable artefact this project can produce, and it is exactly what the previous
four attempts failed to leave behind.

## Consequences

- Writing an ADR is a small tax on every non-trivial change.
- `docs/adr/` becomes the first thing a new contributor — human or agent —
  reads, and it must stay readable, which means keeping ADRs short.
- Merged spike branches that produced no shippable code still produce an ADR,
  so the repository's history reflects effort spent, not just code retained.
