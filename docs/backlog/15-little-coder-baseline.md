---
title: "M4: Run little-coder on the task suite as a baseline"
labels: ["type:chore", "milestone:M4", "area:eval"]
---
`little-coder` is tuned for exactly our model class and is the honest comparison for whether building our own loop bought anything. Run it over the same `tasks/` suite with the same models and record the results next to LIZA's.

The outcome may well be that `little-coder` is simply better. That is informative and acceptable — ADR-0002 chose to own the loop for understandability, not for expected superiority — but it should be measured rather than assumed in either direction.

Done when a written comparison exists in `docs/`, stating plainly whether the velocity metric revealed anything the raw pass/fail did not, including if the answer is no.
