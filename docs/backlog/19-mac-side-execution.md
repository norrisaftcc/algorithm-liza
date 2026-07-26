---
title: "Investigate a narrow Mac-side execution MCP"
labels: ["type:spike", "area:ci"]
---
The agent sandbox cannot reach the Mac at all (ADR-0005): no route to a local inference server, no GitHub credentials, no `gh`. Screen control is not a way around it, because terminals and IDEs are restricted to click-only and shell commands cannot be typed.

What that costs, concretely: `git push` and `gh pr create` stay manual, and the M2 spike (#10 — twenty trials per model measuring native tool-call validity) has to be run by hand. The spike is mechanical, repetitive measurement, which is the strongest argument for automating it.

If this is built, scope it to a named set of commands — `uv run pytest`, `ruff`, `git`, `gh`, `ollama` — inside this repository, not a general shell. There is an obvious irony in granting an agent unrestricted shell on the machine in order to build an agent that ADR-0002 deliberately denies a shell to, and the same reasoning applies to both.

Decide first whether it is worth it at all. A reasonable answer is no: the manual steps are a handful of commands per session, and the security surface is permanent.
