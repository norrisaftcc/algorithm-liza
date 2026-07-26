# Little Coder: Small Models Need Small Harnesses

https://www.youtube.com/watch?v=YH1EjnYFWSU

blurb:

Can a local AI coding agent build a complete full-stack application—without cloud APIs, usage limits, or an internet connection?

In this video, I test Little Coder, an AI coding harness designed specifically for smaller language models, using Qwen 3.6 and Gemma 4. I run both models locally through LM Studio and challenge them to build a full-stack application with a frontend, backend, database, seed data, and authentication.

Along the way, I explain how local LLMs work, what model parameters and quantization mean, how much RAM you need, and why mixture-of-experts models can run much faster than similarly sized dense models. I also walk through the process of downloading a model, starting a local inference server, installing Little Coder, and connecting it to LM Studio.

For the experiment, I compare:

    Qwen 3.6’s speed and ability to work autonomously
    Gemma 4’s slower but more functional final application
    Little Coder’s context management and error-recovery features
    Infinite reasoning loops, syntax errors, and incomplete functionality
    The heat, memory usage, and hardware demands of local AI coding
    Whether local coding models are practical for everyday software development


The results were imperfect—but surprisingly capable. Qwen 3.6 produced an application quickly, although several features and calculations were broken. Gemma 4 created a more functional workflow, but it struggled with basic syntax errors and required help from a frontier coding model before the application would run.

This is not intended to convince you to replace Claude Code, Codex, Gemini CLI, or another cloud-based coding agent. It is an experiment exploring how far local models have come, what Little Coder adds, and whether an entirely offline AI programming workflow is useful today.

Hardware used:

Apple M3 Max with 64 GB of unified memory

Resources:

GitHub repository, prompts, and interactive demos: https://overseedai.github.io/little-c...
Little Coder: https://github.com/itayinbarr/little-...
LM Studio: https://lmstudio.ai/
llama.cpp: https://github.com/ggml-org/llama.cpp

Chapters
00:00 Intro
02:01 Local Models Explained
06:39 Running Models with LM Studio
08:51 Little Coder Harness
11:42 Qwen 3.6 and Gemma 4
12:34 The Experiment - Vacay App
13:11 Qwen 3.6 Run and Results
18:19 Gemma 4 Run and Results
22:55 Recap - The Good
24:21 Recap - The Bad
27:49 Outro
