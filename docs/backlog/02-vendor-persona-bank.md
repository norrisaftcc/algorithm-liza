---
title: "M0: Vendor the capstone persona bank into the repository"
labels: ["type:docs", "milestone:M0", "area:agents"]
---
Ten subagent definitions developed for capstone coursework currently live only in `~/.claude/agents/`, versioned by nothing. Move them under `agents/claude/` verbatim as a historical baseline, with an `agents/README.md` roster that marks which personas are plausibly relevant to LIZA.

Known tone and voice problems are not fixed here — they are fixed later, through review, with the original recoverable from history. Rationale in ADR-0004.

Done when `agents/claude/` holds the ten files unmodified and `agents/README.md` explains the layout and the LIZA/Liza naming collision.
