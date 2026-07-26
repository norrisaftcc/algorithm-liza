---
title: "Investigate a narrow Mac-side execution MCP"
labels: ["type:spike", "area:ci"]
---
The agent sandbox cannot reach the Mac at all (ADR-0005): no route to a local inference server, no GitHub credentials, no `gh`. Screen control is not a way around it, because terminals and IDEs are restricted to click-only and shell commands cannot be typed.

What that costs, concretely: `git push` and `gh pr create` stay manual, and the M2 spike (#10 — twenty trials per model measuring native tool-call validity) has to be run by hand. The spike is mechanical, repetitive measurement, which is the strongest argument for automating it.

If this is built, scope it to a named set of commands — `uv run pytest`, `ruff`, `git`, `gh`, `ollama` — inside this repository, not a general shell. There is an obvious irony in granting an agent unrestricted shell on the machine in order to build an agent that ADR-0002 deliberately denies a shell to, and the same reasoning applies to both.

Decide first whether it is worth it at all. A reasonable answer is no: the manual steps are a handful of commands per session, and the security surface is permanent.

---

**Resolved 2026-07-26: no. Closing as unnecessary.** See
[ADR-0006](../adr/0006-the-mac-is-the-verification-host.md).

The justification above is that the sandbox cannot reach `gh`, `git` or
`ollama`. Work done *on the Mac* reaches all of them — `gh` is authenticated,
`git push` works, and Ollama serves both `gemma4` builds — so the justification
is gone rather than weakened. The M2 spike this item was mainly written to
unblock has since been run on the Mac directly, at 45 model calls
([Spike 001](../spikes/001-gemma4-native-tool-calls.md)).

The security reasoning is still sound, and it was not the deciding factor: this
is dev activity on a dev laptop by the machine's owner, not a service exposed to
anything, and treating it as a boundary needing its own MCP over-weighted the
risk. Keep the narrow-allowlist argument if a *remote* execution surface is ever
proposed — the irony it names, of granting a general shell in order to build an
agent that ADR-0002 deliberately denies a shell to, remains a good argument in
that setting.
