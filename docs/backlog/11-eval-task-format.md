---
title: "M3: Eval task format and the first ten tasks"
labels: ["type:test", "milestone:M3", "area:eval"]
---
A `tasks/` directory where each task is a directory containing a prompt, a pytest file, and a manifest declaring the expected entry point.

Ten tasks minimum, deliberately spanning the range from trivially easy to reliably-failing, so the suite has headroom in both directions. A suite where everything passes and a suite where everything fails are equally uninformative. Draw from real intro-Python coursework: string formatting, loops and conditionals, a small class, file I/O, a recursive function, a function with awkward edge cases.

Done when the tasks exist with their tests, and each test file has been verified against a known-good reference solution.
