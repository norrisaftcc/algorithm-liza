---
title: "M2 spike: Can Gemma 4 emit valid native tool calls through LM Studio?"
labels: ["type:spike", "milestone:M2", "area:core"]
---
Timeboxed to one day. One question: served through LM Studio, does Gemma 4 produce well-formed OpenAI `tool_calls`, and at what rate over ~20 attempts on a fixed prompt? Same measurement for Qwen 3.6 as a control.

This decides whether the `text` protocol is a nice-to-have or the primary path, and it should run before significant effort goes into either.

Per `CONTRIBUTING.md`, this merges as a written record even if the code is discarded. A negative result with a transcript is the deliverable. Write it up in `docs/spikes/`.
