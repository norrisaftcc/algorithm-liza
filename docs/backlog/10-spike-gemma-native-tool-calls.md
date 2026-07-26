---
title: "M2 spike: Can Gemma 4 emit valid native tool calls through LM Studio?"
labels: ["type:spike", "milestone:M2", "area:core"]
---
Timeboxed to one day. One question: served through LM Studio, does Gemma 4 produce well-formed OpenAI `tool_calls`, and at what rate over ~20 attempts on a fixed prompt? Same measurement for Qwen 3.6 as a control.

This decides whether the `text` protocol is a nice-to-have or the primary path, and it should run before significant effort goes into either.

Per `CONTRIBUTING.md`, this merges as a written record even if the code is discarded. A negative result with a transcript is the deliverable. Write it up in `docs/spikes/`.

---

**Run 2026-07-26. Result: positive, 39/40.** See
[Spike 001](../spikes/001-gemma4-native-tool-calls.md).

**The question above was amended before it was answered, and the substitution
matters.** This item names LM Studio and asks for Qwen 3.6 as the control.
Neither was available on the verification host, so the spike ran on **Ollama
0.32.4** with **`gemma4:12b` as the control**. LM Studio remains untested, and
ADR-0002's specific worry — that Gemma-family native tool-call support is
inconsistent *through LM Studio* — is therefore still open. What was measured is
that it is not inconsistent through Ollama: `gemma4:e4b` scored 19/20 and
`gemma4:12b` 20/20 on schema-valid native `tool_calls`.

Still unrun, and now the higher-value question: the **second turn**. This spike
covers a single turn with an empty history. Multi-turn behaviour once
`role: "tool"` results are appended is where ADR-0002 predicts small models
actually break, and it is untested.
