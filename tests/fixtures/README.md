# Stub fixtures

Each file is a scripted conversation replayed by `liza.stub`. The first line is
a header; every line after it is one response.

The `observed` flag in the header is the important field. `true` means the
sequence was lifted from a real transcript recorded against a real model.
`false` means we invented it — it encodes a *belief* about how small models
misbehave, and that belief may be wrong.

Every fixture here is currently `false`. That is expected at M1, since no real
model has been run yet, and it is also the main weakness of this whole
approach: a harness that passes every test below can still fall over on first
contact with Gemma. As real runs accumulate on a machine with an inference
server, transcripts should be promoted into fixtures here and the flag flipped.
When that happens the invented version should be kept if it still describes a
distinct failure, not silently replaced.

| Fixture | What it exercises |
|---|---|
| `happy_path.jsonl` | Tool call, tool result, final answer. The baseline. |
| `malformed_tool_args.jsonl` | `arguments` is not valid JSON. |
| `unknown_tool.jsonl` | A tool name the harness does not implement. |
| `repeated_tool_call.jsonl` | The same call three times, unchanged. |
| `runaway.jsonl` | Never stops calling. Requires a step ceiling to terminate. |
| `prose_instead_of_tool_call.jsonl` | Describes the call in prose instead of emitting one. |
| `truncated_body.jsonl` | Response body stops mid-JSON. |
| `server_error.jsonl` | HTTP 500, as when a server is out of memory. |
| `slow_first_token.jsonl` | A delay before responding, repeated so a retry after a client-side timeout sees it again. |

Two fixtures set `on_exhaustion: repeat_last` rather than the default `error`:
`runaway.jsonl`, because a run with a natural end would not be a runaway, and
`slow_first_token.jsonl`, because a client that times out has still consumed
the turn on the server and a retry must find the same slow response waiting.
Everywhere else, overrunning the script answers HTTP 409 — a test that asks for
more turns than it scripted is nearly always a test with a broken stop
condition, and that should be loud.
