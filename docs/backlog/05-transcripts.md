---
title: "M1: JSONL run transcripts"
labels: ["type:feat", "milestone:M1", "area:core"]
---
Every run writes `.liza/runs/<run-id>.jsonl` containing every request, response, tool call and tool result, with timestamps and token counts where the server reports them.

This is load-bearing for three later things and should not be treated as logging: it is the debugging surface, the input to the growth metrics in ADR-0003, and the fixture source for deterministic tests. Design the record schema deliberately and version it with a `schema` field.

Done when a run produces a transcript that a replay harness can read back and reconstruct the conversation from, byte-identically.
