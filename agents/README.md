# Agents

The persona and skill bank for this project. Rationale and the compile-for-two-
runtimes design are in [ADR-0004](../docs/adr/0004-persona-and-skill-bank.md).

## Naming

**LIZA** in capitals is the local agent harness this repository builds.
`liza-creative-companion` is one persona in the bank below, and a different
thing. The collision is known and tolerated.

## Layout

| Path | Contents |
|---|---|
| `claude/` | The ten capstone subagent definitions, imported verbatim. Historical baseline. |
| `compact/` | *(planned)* Rewritten variants inside LIZA's system-prompt token budget. |
| `skills/` | *(planned)* Task-specific instruction files, loaded on demand. |

## Roster

Imported from `~/.claude/agents/` on 2026-07-26. Each file holds the deployed
prompt, the agent's self-critique of it, and a revised portable version. See
[`claude/INDEX.md`](claude/INDEX.md) for the original index.

| File | Agent | Role | LIZA-relevant? |
|---|---|---|---|
| `clive-prompt-strategist.md` | Clive | Prompt engineering and strategy | Indirectly — for authoring compact variants |
| `linx-wordsmith.md` | Linx | Stylistic writing and editing | No |
| `liza-creative-companion.md` | Liza | Creative ideation | No |
| `kevin-github-algorithm.md` | Kevin | GitHub process, issues, PRs | **Candidate** |
| `scrum-architect-owner.md` | — | Product owner, systems-architecture lens | No |
| `scrum-project-manager.md` | — | Scrum master, GitHub workflow | No |
| `scrum-team-engineer.md` | — | Engineering, review, estimation | Maybe |
| `test-engineer.md` | — | Test authoring and review | **Candidate** |
| `product-acceptance-tester.md` | — | Acceptance testing | Maybe |
| `product-architect-advisor.md` | — | Architecture and product strategy | No |

"LIZA-relevant" is a judgement about which personas describe behaviour a small
local model could plausibly perform on this project's task class. It is not a
ranking of quality, and it will be revised once the eval harness can test the
claim rather than assert it.

## Editing

Files in `claude/` are the imported baseline and are changed only through the
normal review workflow, never rewritten in place to hide a revision. The known
tone and voice problems are real; fixing them is scheduled work, not a
drive-by edit.
