---
title: "M4: Growth velocity scoring and aggregation"
labels: ["type:feat", "milestone:M4", "area:eval"]
---
Depend on `algorithm-shodann` at a pinned commit and score each task's iteration sequence with `composite_score`, producing a self-correction velocity: does LIZA's code improve between attempt n and attempt n+1, and by how much. Aggregate per model and per prompt version.

Do not copy `velocity.py` into this repository. One authoritative scoring implementation shared with the sibling project is most of the value; a fork diverges silently. If the weighting proves wrong for machine-generated code — plausible, since it was tuned for humans learning — tune a local `VelocityConfig` rather than editing the shared maths.

Done when an eval report carries a per-task velocity score and a per-model aggregate.
