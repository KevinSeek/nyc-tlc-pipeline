# 0004 — Extend the foundation phase and push the end date back

**Week:** 2b **Date:** 2026-11-02

## Context

Weeks 1–2 shipped a working walking skeleton (CI → GHCR → homelab timer), but I could not yet explain every line, troubleshoot it, or rewrite it without help. On 2026-10-26 I paused feature work for a 3-day foundation phase (Oct 26–28). The Dockerfile drill alone ran until Nov 2, and `.github/workflows/ci.yml` and `deploy/` (Compose stack, deploy script, systemd service and timer) have not been drilled yet.

## Decision

Extend foundation (Week 2b) to Oct 26–Nov 15 and cover three areas: the Dockerfile, the CI workflow, and the deploy files. Each area is done when I can explain every line, rewrite it from blank, and fix injected faults without notes. Weeks 3–5 shift by the same amount; target completion moves from 2026-11-15 to 2026-12-06. Scope is unchanged.

## Alternatives considered

- Keep 2026-11-15 and cut scope — drops showcase deliverables, and I would still be building on files I cannot defend.
- Defer with no end date until foundation feels done — no forcing function; the charter dates stop meaning anything.
- Drill only the Dockerfile and move on — CI and deploy hold most of my weakest points (CI model, concurrency queue, action pinning, volumes and ownership).

## Plain-language explanation

The pipeline already runs end to end, but I built most of it with heavy help. If an interviewer asks why a line is there, or if it breaks on the homelab, I need to answer and fix it myself. So before adding new features, I am rebuilding my understanding of the parts that ship and run the code: the image recipe, the CI workflow that builds and publishes it, and the homelab setup that pulls and runs it. That costs about three weeks. The project scope stays the same; only the dates move.

## What would make me revisit this

If foundation is not done by 2026-11-15, cut drill depth for the remaining files (explain + fix faults, no rewrite from blank) instead of moving the date again.

## Amendment 2026-11-02

Drill rewrites are not merged as code. Exception: a drill may merge comment-only changes (instructions byte-identical to `main`), because those comments are my own line-by-line explanation (rule 2). First use: Dockerfile comments.

## Amendment 2026-11-05

Second exception: the `ci.yml` drill rewrite merges in full, including two behaviour changes — `astral-sh/setup-uv` v10.3.0 → v10.3.3 and uv pinned with `version: "0.13.1"` (same uv as the image). Both were checked during the drill (SHA verified against the release tag with `git ls-remote`), and they are small enough that a separate step later adds no value. Verification: the PR run (`lint-and-test`) and the first `push` run on `main` after merge (`publish`). Further drill rewrites stay comment-only.
