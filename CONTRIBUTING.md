# Contributing to LIZA

This repository is a research project with a teaching-shaped output. The
workflow below exists so that the *history of the effort* is legible later —
including the parts that did not work. Four earlier attempts at this idea have
no surviving reasoning, only dead code. That is the failure mode we are
designing against.

## The loop

Every change follows the same five steps.

1. **Issue.** Nothing gets built without an issue. The issue states the
   observable outcome, not the implementation. If you cannot write down how
   you will know it worked, it is not ready to be an issue.
2. **Branch.** Cut from `main`, named `<type>/<short-slug>` — for example
   `feat/tool-loop`, `fix/lmstudio-timeout`, `docs/project-setup`,
   `spike/gemma-tool-calling`. One branch per issue.
3. **Commits.** Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`,
   `refactor:`, `chore:`, `spike:`). Small and frequent beats large and tidy —
   iteration count is a signal we deliberately want to keep.
4. **Pull request.** Opened against `main`, linked to its issue with
   `Closes #N`. The PR body follows `.github/PULL_REQUEST_TEMPLATE.md`. CI must
   be green.
5. **Merge.** Squash merge, delete the branch. The issue closes itself.

`main` is always in a state where `liza` starts and the test suite passes.

## Branch types

| Prefix | Use |
|---|---|
| `feat/` | New capability |
| `fix/` | Something behaved incorrectly |
| `docs/` | Documentation and ADRs |
| `test/` | Tests and eval tasks only |
| `refactor/` | Behaviour-preserving change |
| `chore/` | Tooling, CI, dependencies |
| `spike/` | Timeboxed experiment; **may be merged as documentation only** |

## Spikes are first-class

A spike branch answers one question ("can Gemma 4 emit valid OpenAI tool calls
through LM Studio?"). It is timeboxed. When the box expires, the spike is
written up in `docs/adr/` or `docs/spikes/` and merged **even if the code is
thrown away**. A spike that produces a negative result and a written record is
a success. A spike that produces working code and no record is a liability —
that is precisely how the four previous repos ended up unusable.

## Decisions

Anything that constrains future work goes in `docs/adr/` as an ADR. Use
`docs/adr/0002-liza-v0-architecture.md` as the shape. Superseding an ADR means
writing a new one that says so; do not edit history in place.

## Definition of done

A change is done when all of the following hold.

- The behaviour it claims is covered by a test, or by an eval task under
  `tasks/` if the behaviour is model-dependent and therefore not
  deterministically testable.
- `ruff check` and `pytest` pass locally and in CI.
- Anything a future reader would ask "why?" about is answered in a docstring,
  an ADR, or the PR body.
- The issue's stated observable outcome is demonstrably true.

Model-dependent behaviour never gets a hard assertion in the unit suite. It
gets an eval task with a recorded score, because a small local model is a
probabilistic component and pinning it to an exact string produces a suite that
fails for reasons unrelated to our code.

## Local setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/) — on macOS,
`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.

```bash
uv sync
uv run pytest
uv run ruff check
```

The test suite never calls a model. It runs against the stub inference server,
so it works with no GPU, no weights and no network — see
[ADR-0005](docs/adr/0005-development-environment.md).

Exercising LIZA against a *real* model additionally requires a local
OpenAI-compatible inference server — LM Studio, Ollama, or llama.cpp — and is
therefore something only a human on a suitably equipped machine can do. See
`docs/ROADMAP.md` for current status.
