"""M2 spike: does Gemma 4 emit well-formed OpenAI tool_calls through Ollama /v1?

Usage:
    run_spike.py warmup
    run_spike.py native <start_seed> <count>
    run_spike.py text   <start_seed> <count>
    run_spike.py summarise

The model is set by ``LIZA_SPIKE_MODEL`` (default ``gemma4:e4b``) and the
endpoint by ``LIZA_SPIKE_BASE_URL``. The 2026-07-26 run was::

    LIZA_SPIKE_MODEL=gemma4:e4b run_spike.py warmup && ... native 1 20 && ... text 1 5
    LIZA_SPIKE_MODEL=gemma4:12b run_spike.py warmup && ... native 1 20 && ... text 1 5

Every request and response is appended to ``<model>.jsonl``, one JSON object
per line, so a partial run survives. Requests run strictly one at a time --
never parallelise this: the two models do not fit in VRAM together, and
concurrent calls measure eviction thrash rather than the model.

See 001-gemma4-native-tool-calls.md for what this produced.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
BASE_URL = os.environ.get("LIZA_SPIKE_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL = os.environ.get("LIZA_SPIKE_MODEL", "gemma4:e4b")
# One transcript per model, so the two runs never interleave in one file.
LOG = HERE / f"{MODEL.replace(':', '-')}.jsonl"

# ---------------------------------------------------------------- fixed prompt

SYSTEM_PROMPT = (
    "You are LIZA, a coding assistant that works on one small Python task at a "
    "time in a single working directory.\n"
    "You have tools. When you need information about the project, call a tool "
    "instead of guessing. Call exactly one tool at a time and wait for its "
    "result before deciding what to do next.\n"
    "Never invent file contents. If you have not read a file, read it.\n"
    "When the task is done, reply in plain prose with a short summary."
)

USER_PROMPT = "what does hello.py do?"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a text file in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the working directory.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text to a file in the working directory, replacing it if it exists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the working directory.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete new contents of the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List the files and directories at a path in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory to list, relative to the working directory. "
                            "Use '.' for the root."
                        ),
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run pytest against the working directory and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Optional test path to restrict the run to.",
                    }
                },
                "required": [],
            },
        },
    },
]

# The fallback `text` protocol from ADR-0002. Concrete chosen format: a fenced
# block tagged `liza-tool` containing a JSON object with "tool" and "arguments".
TEXT_SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + "\n\n"
    + "You do not have a tool API. To call a tool, emit a fenced code block "
    'tagged `liza-tool` containing a JSON object with exactly two keys: "tool" '
    '(the tool name) and "arguments" (an object of arguments). Emit nothing '
    "else in the message when you call a tool.\n"
    "Example:\n"
    "```liza-tool\n"
    '{"tool": "list_dir", "arguments": {"path": "."}}\n'
    "```\n"
    "The available tools are:\n"
    "- read_file(path: string) -- read a text file.\n"
    "- write_file(path: string, content: string) -- overwrite a text file.\n"
    "- list_dir(path: string) -- list a directory.\n"
    "- run_tests(path: string, optional) -- run pytest.\n"
)

TOOL_SCHEMAS = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS}

# --------------------------------------------------------------- schema check


def validate_args(tool_name: str, args: object) -> tuple[bool, str]:
    """Minimal JSON-Schema check: right keys, right types, no extras."""
    schema = TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        return False, f"unknown tool {tool_name!r}"
    if not isinstance(args, dict):
        return False, "arguments are not a JSON object"
    props = schema["properties"]
    required = schema.get("required", [])
    for key in required:
        if key not in args:
            return False, f"missing required key {key!r}"
    for key, value in args.items():
        if key not in props:
            return False, f"unexpected key {key!r}"
        expected = props[key]["type"]
        if expected == "string" and not isinstance(value, str):
            return False, f"key {key!r} is {type(value).__name__}, want string"
    return True, ""


FENCE_RE = re.compile(r"```liza-tool\s*\n(.*?)\n?```", re.DOTALL)


def parse_text_protocol(content: str) -> tuple[bool, str, object, str]:
    """-> (ok, tool_name, arguments, note)."""
    m = FENCE_RE.search(content or "")
    if not m:
        return False, "", None, "no ```liza-tool fenced block"
    try:
        obj = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        return False, "", None, f"fence body not JSON: {exc}"
    if not isinstance(obj, dict) or "tool" not in obj or "arguments" not in obj:
        return False, "", None, "block missing 'tool'/'arguments'"
    ok, why = validate_args(obj["tool"], obj["arguments"])
    return ok, obj["tool"], obj["arguments"], why


# ------------------------------------------------------------------- plumbing


def log(record: dict) -> None:
    with LOG.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def post(client: httpx.Client, payload: dict) -> tuple[dict | None, float, str]:
    started = time.monotonic()
    try:
        resp = client.post(f"{BASE_URL}/chat/completions", json=payload)
        elapsed = time.monotonic() - started
        if resp.status_code != 200:
            return None, elapsed, f"HTTP {resp.status_code}: {resp.text[:500]}"
        return resp.json(), elapsed, ""
    except Exception as exc:  # noqa: BLE001
        return None, time.monotonic() - started, f"{type(exc).__name__}: {exc}"


def make_client() -> httpx.Client:
    # trust_env=False: see tests/conftest.py -- an exported ALL_PROXY otherwise
    # routes loopback through a proxy and the failure looks like a dead server.
    return httpx.Client(trust_env=False, timeout=300.0)


# -------------------------------------------------------------------- phases


def warmup() -> None:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say OK."}],
        "temperature": 1.0,
        "max_tokens": 16,
    }
    with make_client() as client:
        body, elapsed, err = post(client, payload)
    rec = {
        "phase": "warmup",
        "ts": time.time(),
        "request": payload,
        "latency_s": round(elapsed, 3),
        "error": err,
        "response": body,
    }
    log(rec)
    print(json.dumps({"phase": "warmup", "latency_s": round(elapsed, 3), "error": err}))


def native_trial(client: httpx.Client, trial: int, seed: int) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "tools": TOOLS,
        "temperature": 1.0,
        "seed": seed,
    }
    body, elapsed, err = post(client, payload)

    result = {
        "phase": "native",
        "trial": trial,
        "seed": seed,
        "ts": time.time(),
        "latency_s": round(elapsed, 3),
        "error": err,
        "request": payload,
        "response": body,
    }

    analysis = {
        "http_ok": body is not None,
        "has_tool_calls": False,
        "n_tool_calls": 0,
        "finish_reason": None,
        "args_parsed": False,
        "args_valid": False,
        "tool_name": None,
        "raw_arguments": None,
        "content_text": None,
        "why_invalid": err or "",
        "usage": None,
    }
    if body is not None:
        choice = (body.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        analysis["finish_reason"] = choice.get("finish_reason")
        analysis["usage"] = body.get("usage")
        analysis["content_text"] = msg.get("content")
        calls = msg.get("tool_calls") or []
        analysis["n_tool_calls"] = len(calls)
        analysis["has_tool_calls"] = bool(calls)
        if calls:
            fn = calls[0].get("function") or {}
            analysis["tool_name"] = fn.get("name")
            raw = fn.get("arguments")
            analysis["raw_arguments"] = raw
            parsed = None
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    analysis["args_parsed"] = True
                except json.JSONDecodeError as exc:
                    analysis["why_invalid"] = f"arguments not JSON: {exc}"
            elif isinstance(raw, dict):
                # Ollama sometimes emits arguments as an object, not a string.
                parsed = raw
                analysis["args_parsed"] = True
                analysis["why_invalid"] = "arguments emitted as object, not JSON string"
            else:
                analysis["why_invalid"] = f"arguments is {type(raw).__name__}"
            if analysis["args_parsed"]:
                ok, why = validate_args(analysis["tool_name"], parsed)
                analysis["args_valid"] = ok
                if not ok:
                    analysis["why_invalid"] = why
        else:
            analysis["why_invalid"] = analysis["why_invalid"] or "no tool_calls array"

    result["analysis"] = analysis
    log(result)
    print(
        json.dumps(
            {
                "trial": trial,
                "seed": seed,
                "latency_s": result["latency_s"],
                "finish_reason": analysis["finish_reason"],
                "tool": analysis["tool_name"],
                "valid": analysis["args_valid"],
                "why": analysis["why_invalid"][:80],
            }
        ),
        flush=True,
    )
    return result


def text_trial(client: httpx.Client, trial: int, seed: int) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": TEXT_SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 1.0,
        "seed": seed,
    }
    body, elapsed, err = post(client, payload)
    result = {
        "phase": "text",
        "trial": trial,
        "seed": seed,
        "ts": time.time(),
        "latency_s": round(elapsed, 3),
        "error": err,
        "request": payload,
        "response": body,
    }
    analysis = {
        "http_ok": body is not None,
        "finish_reason": None,
        "block_found": False,
        "block_valid": False,
        "tool_name": None,
        "arguments": None,
        "why_invalid": err or "",
        "usage": None,
    }
    if body is not None:
        choice = (body.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        analysis["finish_reason"] = choice.get("finish_reason")
        analysis["usage"] = body.get("usage")
        content = msg.get("content") or ""
        analysis["block_found"] = bool(FENCE_RE.search(content))
        ok, name, args, why = parse_text_protocol(content)
        analysis["block_valid"] = ok
        analysis["tool_name"] = name or None
        analysis["arguments"] = args
        analysis["why_invalid"] = why
    result["analysis"] = analysis
    log(result)
    print(
        json.dumps(
            {
                "trial": trial,
                "seed": seed,
                "latency_s": result["latency_s"],
                "found": analysis["block_found"],
                "valid": analysis["block_valid"],
                "tool": analysis["tool_name"],
                "why": (analysis["why_invalid"] or "")[:80],
            }
        ),
        flush=True,
    )
    return result


def summarise() -> None:
    native, text = [], []
    for line in LOG.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("phase") == "native":
            native.append(rec)
        elif rec.get("phase") == "text":
            text.append(rec)
    out = {
        "native_trials": len(native),
        "has_tool_calls": sum(r["analysis"]["has_tool_calls"] for r in native),
        "finish_reason_tool_calls": sum(
            r["analysis"]["finish_reason"] == "tool_calls" for r in native
        ),
        "args_parsed": sum(r["analysis"]["args_parsed"] for r in native),
        "args_valid": sum(r["analysis"]["args_valid"] for r in native),
        "tools_chosen": {},
        "latency_median": None,
        "latency_min": None,
        "latency_max": None,
        "multi_call_trials": sum(r["analysis"]["n_tool_calls"] > 1 for r in native),
        "failures": {},
        "text_trials": len(text),
        "text_block_found": sum(r["analysis"]["block_found"] for r in text),
        "text_block_valid": sum(r["analysis"]["block_valid"] for r in text),
        "text_tools_chosen": {},
        "text_latency_median": None,
        "text_failures": {},
        "prompt_tokens": None,
        "completion_tokens_median": None,
    }
    for r in native:
        n = r["analysis"]["tool_name"] or "<none>"
        out["tools_chosen"][n] = out["tools_chosen"].get(n, 0) + 1
        if not r["analysis"]["args_valid"]:
            why = r["analysis"]["why_invalid"] or "unknown"
            out["failures"][why] = out["failures"].get(why, 0) + 1
    for r in text:
        n = r["analysis"]["tool_name"] or "<none>"
        out["text_tools_chosen"][n] = out["text_tools_chosen"].get(n, 0) + 1
        if not r["analysis"]["block_valid"]:
            why = r["analysis"]["why_invalid"] or "unknown"
            out["text_failures"][why] = out["text_failures"].get(why, 0) + 1
    if native:
        lat = sorted(r["latency_s"] for r in native)
        out["latency_median"] = round(statistics.median(lat), 2)
        out["latency_min"], out["latency_max"] = lat[0], lat[-1]
        usages = [r["analysis"]["usage"] for r in native if r["analysis"]["usage"]]
        if usages:
            out["prompt_tokens"] = sorted({u.get("prompt_tokens") for u in usages})
            out["completion_tokens_median"] = statistics.median(
                u.get("completion_tokens", 0) for u in usages
            )
    if text:
        out["text_latency_median"] = round(
            statistics.median(r["latency_s"] for r in text), 2
        )
    print(json.dumps(out, indent=2))


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "warmup":
        warmup()
        return
    if cmd == "summarise":
        summarise()
        return
    start_seed, count = int(sys.argv[2]), int(sys.argv[3])
    fn = native_trial if cmd == "native" else text_trial
    with make_client() as client:
        for i in range(count):
            fn(client, start_seed + i, start_seed + i)


if __name__ == "__main__":
    main()
