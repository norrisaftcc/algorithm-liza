---
title: "M1: Agent loop with the native tool protocol"
labels: ["type:feat", "milestone:M1", "area:core"]
---
The core loop: send messages, receive a response, dispatch any tool calls, append results, repeat until the model answers or a step limit is hit. Native OpenAI-style `tool_calls` only — the `text` protocol is issue for M2.

Guard rails the loop needs from the start, because small models hit all of them: a hard step ceiling, detection of a model repeating an identical tool call, and a clear error when the model emits malformed tool arguments rather than a stack trace.

Done when `liza --provider lmstudio "read hello.py and tell me what it does"` completes a request -> tool call -> tool result -> answer cycle against a local model.
