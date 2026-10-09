# 0001 — HTTP client for downloading TLC files: httpx

**Week:** 1  **Date:** 2026-10-09

## Context
Ingestion downloads one monthly Parquet file (~50 MB) from the NYC TLC site. A stalled download must fail rather than hang, so the orchestrator can retry it. I needed an HTTP client that makes that behaviour easy to get right.

## Decision
Use `httpx`, pinned `>=0.28.1,<0.29`, with the exact version locked in `uv.lock`. Downloads are streamed to disk, and the timeout is set explicitly in code.

## Alternatives considered
- `requests` — the most widely known option, but it has no default timeout (`timeout=None`), so a forgotten argument means a request can hang forever.
- `urllib` (standard library) — no extra dependency, but a lower-level API and more code for streaming and error handling.

## Plain-language explanation
I chose httpx because it times out by default, so a stalled download fails and Prefect can retry it instead of hanging forever. With `requests`, every call needs a `timeout` argument, and forgetting one is a silent bug. I still set the timeout explicitly, because the 5-second default is a safety net, not a value chosen for this source. httpx also has streaming downloads built in, so a large file is written to disk in chunks instead of being held in memory. It is still pre-1.0, so I pin it below the next minor version, and the lockfile fixes the exact version.

## What would make me revisit this
httpx 1.0 changes its API, or the pin blocks a security fix.
