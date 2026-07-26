---
title: "M3: Eval runner and JSON report"
labels: ["type:feat", "milestone:M3", "area:eval"]
---
`liza-eval --model <m> --protocol <p>` runs the full task suite unattended in isolated working directories and emits a JSON report: per task, pass/fail, iteration count, wall time, token counts, and the transcript path.

Unattended is the operative word. A local model will hang, loop, and produce output that crashes the harness; the runner has to survive all three and record them as results rather than aborting the suite. Per-task timeouts are mandatory.

Done when a full suite run completes against a local model without supervision and the report is diffable between runs.
