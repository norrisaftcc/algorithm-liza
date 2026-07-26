---
title: "M2: File tools — read_file, write_file, list_dir"
labels: ["type:feat", "milestone:M2", "area:tools"]
---
Three of the four v0 tools from ADR-0002. All paths resolve inside the working directory and escape attempts are refused with a message the model can act on, not an exception.

Read-before-edit is worth adopting from `little-coder`: requiring a file to have been read before it can be written catches the common small-model failure of confidently rewriting a file it has only guessed the contents of.

Tool descriptions are system prompt tokens and the budget is tight. Write them terse and count them.

Done when all three tools are exercised end to end by a local model and covered by replay tests.
