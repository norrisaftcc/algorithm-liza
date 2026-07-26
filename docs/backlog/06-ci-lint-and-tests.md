---
title: "M1: CI running ruff and pytest"
labels: ["type:chore", "milestone:M1", "area:ci"]
---
A GitHub Actions workflow on pull requests: `uv sync`, `ruff check`, `pytest`. No inference server is available on a runner, so the suite must pass without one — which is the forcing function that keeps model-dependent behaviour out of the unit tests and in the eval harness where it belongs.

Done when CI is green on a pull request and required for merge.
