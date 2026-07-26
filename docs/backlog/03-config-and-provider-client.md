---
title: "M1: Config and OpenAI-compatible provider client"
labels: ["type:feat", "milestone:M1", "area:core"]
---
A `pydantic` config object and an `httpx` client that speaks `/v1/chat/completions` against a configurable base URL, with named presets for LM Studio (`127.0.0.1:1234`), Ollama (`127.0.0.1:11434`) and llama.cpp (`127.0.0.1:8888`), each overridable by environment variable. Local servers ignore the API key but usually require one to be present, so send a placeholder.

Timeouts matter more here than for cloud providers: a 4B model on a loaded laptop can take a long time to first token, and a default 30s timeout will produce failures that look like harness bugs.

Done when a smoke script gets a completion back from a running LM Studio server, and the client's request construction is unit-tested against a recorded response with no server running.
