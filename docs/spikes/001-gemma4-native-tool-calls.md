# Spike 001: Does Gemma 4 emit valid native tool calls?

- **Question from:** [`docs/backlog/10-spike-gemma-native-tool-calls.md`](../backlog/10-spike-gemma-native-tool-calls.md)
- **Date:** 2026-07-26
- **Result:** Yes — 39/40 trials across two builds. Native is the primary path.
- **Transcripts:** [`gemma4-e4b.jsonl`](gemma4-e4b.jsonl), [`gemma4-12b.jsonl`](gemma4-12b.jsonl)
- **Driver:** [`run_spike.py`](run_spike.py)

## What was actually run, versus what was filed

The backlog item asks about **Gemma 4 through LM Studio, with Qwen 3.6 as a
control**. Neither was available. This ran on **Ollama 0.32.4**, and the control
is **`gemma4:12b`** rather than Qwen, because those are the models on the
machine. The item should be amended rather than left to imply a question this
write-up did not answer — the substitution changes what the result generalises
to, and Ollama's protocol deviations (below) are specific to Ollama.

One fixed system prompt and one fixed `tools` array, held byte-identical across
every trial and across both models. The tool set is ADR-0002's v0 four:
`read_file`, `write_file`, `list_dir`, `run_tests`, each with a real JSON-Schema
`parameters` block. User turn: *"what does hello.py do?"*. Temperature 1.0
(Ollama's declared default for this model), seed varied 1..20 as the only
per-trial change. Cold-load time was measured by a separate warmup request and
excluded from every trial timing.

## Results

| | `gemma4:e4b` (8.0B) | `gemma4:12b` (11.9B) |
|---|---|---|
| Native trials | 20 | 20 |
| `finish_reason: "tool_calls"` | 20/20 | 20/20 |
| `arguments` parsed as JSON | 20/20 | 20/20 |
| Arguments validated against schema | **19/20** | **20/20** |
| **End-to-end validity** | **95%** | **100%** |
| Median latency | 2.37 s | 6.10 s |
| Cold load | 6.05 s | 7.94 s |
| Text-protocol fallback | 5/5 | 5/5 |
| Text median latency | 3.63 s | 12.55 s |
| Prompt tokens (native / text) | 406 / 285 | 406 / 285 |

Zero malformed-JSON events. Zero hallucinated tool names. Zero multi-call
responses. Zero cases of the model narrating a tool call in prose instead of
emitting one — the failure mode `prose_instead_of_tool_call.jsonl` was invented
to model never occurred in 40 trials.

The single failure was **semantic, not serialisational**: `gemma4:e4b` trial 9
called `list_dir` with `{}`, omitting the required `path`. Its own `reasoning`
text contained a correct plan ("list the files in the current directory") that
it then failed to serialise into an argument. `finish_reason` was still
`tool_calls` and the JSON still parsed — only the schema check caught it.

With n=20 each, 20/20 versus 19/20 **is not a meaningful difference** and must
not be used to justify the 12B's memory footprint. The 12B is also ~2.6x slower
per turn.

## Ollama deviates from the OpenAI response schema in ways that will break a strict parser

All four were present in every native response, and all are visible in the
transcripts. These matter directly for backlog item 03, the provider client:

1. **A non-standard `message.reasoning` field**, alongside `content` and
   `tool_calls`. A pydantic model with `extra="forbid"` rejects **every single
   response**. It is also genuinely useful transcript material — capture it
   rather than discard it.
2. **`content` is `""`, not `null`**, when a tool call is present. Any branch
   written as `if message.content is None: # it's a tool call` takes the wrong
   path 100% of the time. Branch on the presence of `tool_calls` instead.
3. **`tool_calls[].index` is present**, which OpenAI emits only in streaming
   deltas. Same forbid-extras hazard.
4. `system_fingerprint` is the literal `"fp_ollama"`; ids look like
   `call_1lw82e7d`; there is no `refusal` field. **Do not assert on id values in
   fixtures.**

`function.arguments` was correctly a JSON-encoded **string** in 40/40 — the
known Ollama quirk of returning an object never fired on 0.32.4. Keep the
defensive branch anyway.

## The text protocol scored 5/5, and that number is less transferable than it looks

Ollama strips the model's reasoning out of `content` into the separate
`reasoning` field. That is *why* `content` in the text trials was a bare fenced
block with no surrounding prose, and why the parse was perfect. A provider that
inlines reasoning into `content` — llama.cpp and LM Studio can, depending on
configuration — would hand LIZA prose wrapped around the fence, and 5/5 would
not survive. **The text result is more provider-dependent than the native one.**

## What this does not measure

The honest caveat, and it is a large one. This is **one fixed single-turn
prompt with an empty conversation history** — exactly what the spike asked for,
and nothing more.

- It does not measure whether the model picks the *right* tool. `gemma4:12b`
  chose `list_dir {"path": "."}` in all 25 trials, never `read_file("hello.py")`
  despite the user naming the file. Defensible as "look before you read", but it
  means the 20/20 rests on a single decision made identically every time.
- It does not measure recovery from a tool result, or survival across multi-turn
  context growth. **That is where ADR-0002 predicts small models actually break**,
  and it is untested here.

Sampling did vary — all 20 of the 12B's `reasoning` strings were distinct, and
completion tokens ranged 43–83. The model simply converged on the same
structured output regardless.

**The obvious next spike is the second turn:** append a `role: "tool"` result
and measure whether the model stays coherent.

## Recommendation

Make `native` the default protocol for this model family. Keep `text` as a thin
fallback for models with no `tools` capability, rather than as the co-equal
implementation ADR-0002 specifies. ADR-0002 called the eventual deletion of one
protocol "a success condition, not waste" — this is the first evidence pointing
at which one.

Make the loop resilient to the observed failure mode rather than switching
protocols to avoid it: a missing required argument should produce a tool-result
error fed back to the model, not a crash.

ADR-0002's stated worry — that "Gemma-family models served through LM Studio
have inconsistent native tool-call support" — **does not hold for these builds on
Ollama**. It may still hold on LM Studio, which is untested.
