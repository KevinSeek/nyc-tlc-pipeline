# 0003 — Pull-based deploy: timer vs Watchtower vs push

**Week:** 2  **Date:** 2026-10-24

## Context
Every merge to `main` publishes the pipeline image to GHCR with a full-SHA tag and a moving `main` tag. The homelab must pick up the new image and prove it runs, without inbound exposure and without me SSHing in. The `pipeline` service is a one-off job (`profiles: [manual]`), not a long-running container, so "deploy" means "run the new image once and check it", not "restart a service".

## Decision
- A systemd timer (`nyc-tlc-deploy.timer`, every 15 min) runs `deploy/deploy.sh` as the `deployer` user.
- The script always pulls `pipeline` at the tag set by `IMAGE_TAG` in `.env` (`main` by default), then compares the local image ID before and after the pull. Only if the ID changed does it run the smoke flow once with `docker compose run --rm -T pipeline`. A pull failure keeps the current image and exits 1. All output goes to journald, and the run appears in Prefect UI history.
- Rollback: set `IMAGE_TAG` in `.env` to a full commit SHA. The next tick pulls that tag, sees a changed image ID and runs the smoke flow against it. `docker compose run --rm pipeline` runs it immediately instead of waiting. Set `IMAGE_TAG=main` again to return to `main`. There is no `docker compose up -d` step: `profiles: [manual]` means `up -d` never starts `pipeline`.
- Trade-off: a failed smoke run is reported only once. The failed image stays pulled, so the next tick sees no change, logs `deploy: no change` and exits 0. While `IMAGE_TAG` is pinned, new merges to `main` are ignored until I unpin.

## Alternatives considered
- Watchtower — it restarts long-running containers when their image changes. `pipeline` is a one-off job that `up -d` never starts, so there is nothing for it to restart, and it has no step to run and check the smoke flow. The charter also requires a deploy script I wrote myself.
- Push-based (CI SSHes into the homelab after publishing) — needs inbound access to the homelab or a self-hosted runner, and it puts homelab credentials in GitHub. Charter §3 rules out both. Parked in `docs/LATER.md` (Cloudflare Tunnel variant).
- Manual pull over SSH — works, but nothing proves a merge reached the homelab, and charter §3 rules out manual SSH deploys.

## Plain-language explanation
Every 15 minutes the homelab asks GHCR for the image tag named in `.env`. If the image it gets back differs from the one it already had, it runs the smoke flow once and logs whether it passed; otherwise it does nothing. Nothing reaches into the homelab from outside, and there is no third-party updater. Rolling back is a one-line change: pin an older commit SHA in `.env`, and the next check runs that version. The weak spot is that a failed smoke run is reported only once. After that, the homelab keeps the failed image and treats it as current.

## What would make me revisit this
The real scheduled flow (Week 5) runs from this image: a failed smoke run must then block it or keep alerting, not be reported once and forgotten.
