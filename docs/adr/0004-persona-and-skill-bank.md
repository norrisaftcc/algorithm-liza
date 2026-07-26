# ADR-0004: A persona and skill bank owned by this repository

- **Status:** Accepted
- **Date:** 2026-07-26
- **Deciders:** @norrisaftcc

## Context

A roster of ten subagent definitions already exists, developed for capstone
course work and currently living in `~/.claude/agents/`. Each file carries the
originally deployed prompt, a self-critique, and a revised, de-course-ified
prompt. They cover prompt strategy (Clive), stylistic editing (Linx), creative
ideation (Liza), GitHub process enforcement (Kevin), and a Scrum-shaped
production set — product owner, project manager, engineer, test engineer,
acceptance tester, architecture advisor.

They are useful, they are ours, and right now they exist only in a dotfile
directory on one machine, versioned by nothing. That is the same failure mode
[ADR-0001](0001-record-architecture-decisions.md) is about. They have also
acknowledged tone and voice problems that will only get fixed if they are
somewhere that supports review and iteration.

There is a real design question underneath the housekeeping one. LIZA needs a
system prompt, and the natural instinct is to reach for these. That instinct is
wrong as stated: these prompts run 1,500–3,000 tokens each, and
[ADR-0002](0002-liza-v0-architecture.md) commits us to a small-model budget
where `little-coder` gets competitive results at roughly 1,000 tokens of system
prompt and a 7k cold start. Dropping a 3,000-token persona onto a Gemma-class
model does not give it a personality; it gives it less room to think.

A naming collision is also worth stating plainly: the existing `Liza` persona
is a creative-ideation agent, while LIZA in this repository is the local agent
harness. They are not the same thing and the docs must not pretend otherwise.

## Decision

Establish `agents/` as the versioned home of the persona and skill bank.

**`agents/claude/`** holds the ten definitions verbatim as imported, as the
historical baseline. They are not edited in place; improvements land as
reviewed changes with the original recoverable from history.

**Personas are authored once and compiled for two runtimes.** A persona's
source is a Markdown file with YAML frontmatter — `name`, `description`,
`model`, `tags`, and a `budget` field giving a target token ceiling. From that
source we produce a Claude Code subagent file and, where the persona is
relevant to LIZA, a **compact variant** under the ADR-0002 token budget. The
compact variant is a rewrite, not a truncation: for a small model, "how you
work" instructions in four numbered steps outperform four paragraphs of
character description, and most of what makes these prompts good for Claude is
exactly the nuance a 4B model will drop.

**Not every persona gets a compact variant.** Kevin (GitHub process) and the
test engineer plausibly map onto real LIZA behaviours. Liza-the-creative-
companion does not, and forcing it would be cargo cult.

**Skills live in `agents/skills/`**, in the same spirit: a task-specific
Markdown instruction file, loaded on demand rather than resident in the system
prompt. This is the mechanism `little-coder` uses (thirty skill files, loaded
situationally, kept out of cold start) and it is the right answer to "we want
more instruction than the token budget allows".

**No course-specific content.** The imported revised prompts already had
hardcoded course assumptions stripped, and the bank should stay portable.

## Consequences

- Compiling one source into two targets needs a small build step and a check
  that compiled outputs are current. That is real work; it is scheduled as its
  own issue rather than smuggled into another change.
- Compact variants will be measurably worse than their full versions at nuanced
  judgement. The eval harness is where we find out whether they are good enough
  for the task class LIZA actually targets.
- Ten personas is more than this project needs today. The bank is a library, not
  a manifest of things to build; only Kevin and the test engineer are candidates
  for near-term LIZA use.
- The `Liza` / LIZA name collision persists. Documentation resolves it by
  convention: **LIZA** in capitals is the harness, `liza-creative-companion` is
  the persona, and the persona should be renamed if the ambiguity causes a real
  mistake.
