---
title: "Persona source format and the compile step"
labels: ["type:feat", "area:agents"]
---
A single authored source per persona — Markdown with YAML frontmatter carrying `name`, `description`, `model`, `tags` and a `budget` token ceiling — compiled into a Claude Code subagent file and, where relevant, a compact variant for LIZA.

Needs a build command and a CI check that compiled outputs are current, otherwise the two copies drift and the source stops being authoritative.

Blocked on M2: there is no point defining a token budget for a system prompt LIZA does not yet have. Rationale in ADR-0004.
