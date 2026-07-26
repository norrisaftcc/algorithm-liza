---
title: "M2: The text tool protocol"
labels: ["type:feat", "milestone:M2", "area:core"]
---
A second tool protocol that parses fenced blocks out of ordinary prose, selectable with `--protocol text`, running the same tool set as `native`.

The reason this exists is diagnostic as much as functional: when a Gemma-class model fails a task, we currently cannot tell whether the harness is wrong, the model cannot reason about the task, or the model simply cannot serialise a tool call. Two protocols separate the third cause from the first two.

Parsing must be forgiving — wrong fence language tags, missing closing fences, and prose wrapped around the block are all normal small-model output, and a strict parser will attribute model competence problems to formatting.

Done when both protocols complete the same task and both transcripts are committed as fixtures.
