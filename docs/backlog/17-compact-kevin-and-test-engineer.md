---
title: "Write compact variants of Kevin and the test engineer"
labels: ["type:docs", "area:agents"]
---
The two personas that plausibly describe behaviour a small local model could perform on this project's task class: Kevin (GitHub process, issues, PRs) and the test engineer.

The compact variant is a rewrite, not a truncation. The imported prompts run 1,500-3,000 tokens; ADR-0002's budget is roughly a thousand for the entire system prompt. Most of what makes these prompts good for Claude is precisely the nuance a 4B model drops on the floor, and for a small model four numbered "how you work" steps outperform four paragraphs of character description.

Whether the compact variants are good enough is an eval question, not an opinion — so this is blocked on M3.
