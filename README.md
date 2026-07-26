# LIZA

**Local Intuitive Zoetropic Agent** (or Lateral Intuitive Zoetropic Agent).

This began as a bit of fun — can local models run the personae of a few of my
agents with reasonable success? Now that we're serious about it, it needs a
proper design.

## What LIZA is for

A code assistant driven by a model running on the laptop in front of you, aimed
at a deliberately narrow task: write or repair a single small Python program,
function, or module, of the kind assigned in an introductory or intermediate
course.

The narrowness is the design. Small models are not small frontier models — they
are a different component, with different failure modes, and they fall apart on
"build this system" in ways they do not on "write this function". Four previous
attempts at this idea produced four repositories that do not work. This one
starts by writing down why it is built the way it is, so that the next person
to read it — possibly LIZA — inherits the reasoning and not just the wreckage.

## Definition of done, early version

LIZA is usable as a simple code assistant with a local model: given a spec and
a failing test, she writes the module, runs the tests, reads the failure, and
revises — unaided. That is milestone M2. Everything after it is measurement.

## Start here

| Document | What it covers |
|---|---|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Milestones M0–M4, each with a checkable definition of done, and what is deliberately fenced off |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | The issue → branch → PR loop, and why spikes merge even when the code is discarded |
| [`docs/adr/`](docs/adr/) | Architecture decisions. [0002](docs/adr/0002-liza-v0-architecture.md) is the one to read first |
| [`docs/backlog/`](docs/backlog/) | The seeded work items, filed as issues by `scripts/seed-issues.sh` |
| [`docs/spikes/`](docs/spikes/) | Timeboxed experiments and their transcripts. [001](docs/spikes/001-gemma4-native-tool-calls.md) measures whether Gemma 4 emits valid native tool calls |
| [`agents/`](agents/) | The persona and skill bank |

## Related projects

[**little-coder**](https://github.com/itayinbarr/little-coder) — a coding agent
tuned for small local models, and the closest prior art to what LIZA is trying
to do. LIZA does not fork it; it is installed as the baseline we benchmark
against, on the grounds that a harness we cannot read teaches us nothing about
the loop. See [ADR-0002](docs/adr/0002-liza-v0-architecture.md).

[**algorithm-shodann**](https://github.com/norrisaftcc/algorithm-shodann) — a
CI bot that scores *growth velocity*: the delta between submissions rather than
absolute quality. Its scoring module is applied to the code LIZA generates, to
answer whether she improves her own work between attempts.
[ADR-0003](docs/adr/0003-adopt-shodann-growth-metrics.md) explains why that
application is a better fit than pointing it at our own pull requests.

The four earlier attempts are not linked, because none of them work. LIZA can
pillage them for ideas once she runs — a good first real task, and a bad first
dependency.

## Naming

**LIZA** in capitals is this harness. `liza-creative-companion` in
[`agents/`](agents/) is a Claude subagent persona for creative ideation, and a
different thing entirely.
