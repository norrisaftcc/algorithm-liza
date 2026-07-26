---
title: "M1: Fixture-driven stub inference server"
labels: ["type:feat", "milestone:M1", "area:core", "area:eval"]
---
An OpenAI-compatible `/v1/chat/completions` endpoint that replays a scripted sequence of responses from a fixture file, so the harness can be developed and tested with no model and no GPU.

This is not only a workaround for the sandbox having no model (see ADR-0005). The responses we most need to survive are the ones a real small model emits *occasionally and unpredictably*: malformed tool-call arguments, a truncated JSON body, the same tool call repeated forever, a run that never terminates, a tool name that does not exist, and a reply that ignores the tool protocol entirely and answers in prose. Provoking those on demand from Gemma is not a workable test strategy; replaying them deterministically on every CI run is.

Fixtures are JSONL and share the transcript schema, so a real run recorded on the Mac can be replayed back as a fixture without conversion. Fixtures invented rather than observed should be commented as such, because a stub encodes our beliefs about model behaviour and those beliefs will be wrong in places.

Done when the stub drives a full multi-turn tool cycle, the pathological cases above each have a fixture, and the unit suite uses it exclusively.
