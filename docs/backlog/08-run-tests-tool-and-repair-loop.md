---
title: "M2: run_tests tool and the edit-test-repair loop"
labels: ["type:feat", "milestone:M2", "area:tools"]
---
The fourth v0 tool: run `pytest` against a fixed path and return the result. Deliberately not a shell — narrow enough to be safe, and the only execution feedback this task class needs.

The interesting part is what comes back. Raw pytest output is long, and most of it is noise that will crowd a small context window. Truncate and summarise: the failing test name, the assertion, and the relevant traceback frame. How aggressively to trim is an empirical question the transcripts will answer.

Done when, given a spec and a failing test file, LIZA writes a module, runs the tests, reads the failure and revises — at least one unaided cycle against a local model. **This is the project's early definition of done.**
