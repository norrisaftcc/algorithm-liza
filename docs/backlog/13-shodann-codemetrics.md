---
title: "M4: Emit SHODANN-shaped CodeMetrics from eval runs"
labels: ["type:feat", "milestone:M4", "area:eval"]
---
Per task iteration, extract `coverage`, `test_count`, `complexity`, `loc`, `functions`, `docstrings`, `lint_issues` and `syntax_errors` from LIZA's generated code, using SHODANN's field names exactly.

Generated code frequently does not parse, so the extractor has to handle that as data rather than as an exception — `syntax_errors` is a field for exactly this reason, and a run producing broken code should score badly rather than crash the harness.

This is worth doing on its own merits even if the scoring in the next issue is later dropped. Rationale in ADR-0003.
