Seeds the repository. No issue to close — this branch is what creates them.

## What changed

Everything a contributor needs before any code exists:

- `README.md` — what LIZA is, and the narrowness that is the design rather than a
  limitation of it.
- `CONTRIBUTING.md` — the issue → branch → commits → PR → squash-merge loop,
  branch type prefixes, and a definition of done that treats spikes as
  first-class: a timeboxed spike merges as documentation even when its code is
  thrown away.
- `docs/adr/0001` … `0005` — the reasoning behind the architecture, the metrics
  question, the persona bank, and the two-machine development split.
- `docs/ROADMAP.md` — M0 through M4, with the early definition of done pinned at
  M2 (LIZA writes and repairs code) rather than at "it runs".
- `agents/` — the capstone-course persona bank, vendored verbatim under
  `agents/claude/` with an index and an honest per-persona note about whether it
  is relevant to LIZA.
- `docs/backlog/01-19.md` and `scripts/seed-issues.sh` — nineteen issues written
  as files with YAML frontmatter, plus an idempotent script that files them on
  GitHub.
- `.github/` issue and PR templates.

## Why this shape

Four earlier repositories tried fragments of this and none of them work. The
code from those attempts survives; the reasoning does not, which is why none of
it can be salvaged with any confidence. ADR-0001 exists to stop that happening a
fifth time, and it is the reason the ADRs carry negative results with the same
weight as decisions.

The backlog lives in the repository as well as on GitHub because the environment
this was authored in cannot reach the GitHub API. Rather than lose the issue
text, it is written to files that `scripts/seed-issues.sh` turns into real
issues. That has a side benefit worth keeping: the issue text is reviewable in a
diff.

Two decisions in here are load-bearing and easy to miss in the diff:

- **We own the agent loop.** little-coder is the benchmark baseline we measure
  against, not a codebase to fork. The whole loop is under 300 lines; a framework
  would cost more in indirection than it saves. See ADR-0002.
- **SHODANN's growth-velocity metrics are adopted against the code LIZA
  generates, not against our own pull requests.** Applying them to us would make
  us both instrument and subject, and greenfield deltas from zero are large,
  flattering and uninformative. Applying them to iterations of model-written code
  asks a question the metric actually answers: did the model improve its own code
  after seeing the test fail? See ADR-0003.

## How this was verified

No code to test. `scripts/seed-issues.sh --dry-run` parses all nineteen backlog
files and reports the labels it would create. The Python version floor was
checked for consistency across `pyproject.toml`, both ADRs and `CONTRIBUTING.md`
after ADR-0005 lowered it to 3.10 — one stale reference was found that way and
fixed in 5f615e2.

## Definition of done

- [x] Behaviour is covered by a test, or by an eval task if it is model-dependent — n/a, no behaviour yet
- [x] `ruff check` and `pytest` pass — n/a, no code yet
- [x] Reasoning is captured in a docstring, an ADR, or this PR body
- [x] The linked issue's stated outcome is demonstrably true — this branch creates the issues
