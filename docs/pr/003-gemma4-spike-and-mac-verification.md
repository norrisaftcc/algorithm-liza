spike: Gemma 4 emits valid native tool calls (39/40), and the Mac is the verification host

Closes ISSUE_10. Closes ISSUE_19.

## What this is

Two things that turned out to be the same thing: the M2 spike finally ran, and
the reason it could run is that it ran on the Mac, which invalidates how
ADR-0005 framed the project's environment.

## The spike

[`docs/spikes/001-gemma4-native-tool-calls.md`](../spikes/001-gemma4-native-tool-calls.md),
with both raw transcripts and the driver script committed alongside it.

| | `gemma4:e4b` | `gemma4:12b` |
|---|---|---|
| Schema-valid native `tool_calls` | 19/20 | 20/20 |
| `arguments` parsed as JSON | 20/20 | 20/20 |
| Median latency | 2.37 s | 6.10 s |
| Text-protocol fallback | 5/5 | 5/5 |

ADR-0002's worry that Gemma-family native tool-call support is unreliable does
not hold for these builds on Ollama. It may still hold on LM Studio, which is
untested — the backlog item asked for LM Studio and Qwen 3.6, and got Ollama
and `gemma4:12b`, because that is what the machine has. The item has been
amended to say so rather than letting the write-up silently answer a different
question.

The one failure was semantic, not serialisational: a `list_dir` call with `{}`,
omitting the required `path`. The right response is a tool-result error fed back
to the model, not a protocol switch.

**Three Ollama deviations that will break a strict provider client**, all in
every response, all relevant to issue #3: a non-standard `message.reasoning`
field, `content` as `""` rather than `null` on tool calls, and
`tool_calls[].index`. A pydantic model with `extra="forbid"` rejects every
single response.

## The ADR

[`docs/adr/0006-the-mac-is-the-verification-host.md`](../adr/0006-the-mac-is-the-verification-host.md)
amends ADR-0005, whose environment findings are stated as flat facts about "the
environment" but are properties of the **agent sandbox**. On the Mac, `gh` is
authenticated, `git push` works, and Ollama serves both models. ADR-0005's
Status line now points forward; its body is untouched, per ADR-0001.

Backlog #19 (Mac-side execution MCP) is closed as unnecessary — its entire
justification was that the sandbox cannot reach `gh`, `git` or `ollama`, and
work done on the Mac reaches all three. The security reasoning was sound but was
not the deciding factor; it is preserved in the item for the remote case.

ADRs 0002–0005 were still marked `Status: Proposed` despite being merged and
implemented, which makes a binding decision indistinguishable from a draft.
Flipped to `Accepted` — Status is the one mutable field per ADR-0001.

## Not done here

- **The second turn is untested.** This spike is one single-turn prompt with an
  empty history. Multi-turn behaviour once `role: "tool"` results are appended is
  where ADR-0002 predicts small models break. That is the next spike, and it is
  worth more than this one was.
- **The transcripts are not yet promoted to `tests/fixtures/`.** Doing so will
  fail `test_fixture_provenance_is_declared` by design. Separate change.
- Spike 001 found that none of the four invented failure-mode fixtures occurred
  in 40 trials. The fixture set over-represents serialisation failure relative to
  what these models actually do.

## Checklist

- [x] `ruff check` and `pytest` pass locally (26 passed; no CI exists — see #6)
- [x] The reformatted tool descriptions in `run_spike.py` were verified
      byte-identical to what was actually sent, by diffing against both recorded
      transcripts
- [x] Reasoning recorded in an ADR and a spike write-up
- [ ] CI green — **not possible; there is no CI.** Backlog #6 is open and
      unimplemented, and all three prior PRs merged with zero checks
