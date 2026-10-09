# nyc-tlc-pipeline — Project Charter

**Status:** FROZEN as of 2026-10-09
**Owner:** Kevin
**Target completion:** 2026-11-15 (Sunday)

> Monthly NYC TLC trip files ingested incrementally into a DuckDB warehouse, transformed and tested with dbt, orchestrated by Prefect, shipped as a Docker image via GitHub Actions, and run on a schedule in the homelab.

---

## 1. Scope

### In scope

| Layer | Deliverable | What it proves |
|---|---|---|
| Ingestion (Python) | Download a monthly Parquet → checksum → land raw file in `data/raw/` → load to `raw` schema in DuckDB. **Manifest table** records month, load time, row count, file hash. | Idempotent + incremental loads, backfills, re-published file handling |
| Validation | Schema/type checks at load time; failed files are moved to `data/quarantine/`, not loaded | Failing early at the source |
| dbt | `staging` → `intermediate` → **max 3 marts** | Layering, `source`/`ref`, incremental models |
| Tests | Generic tests + source freshness + **2–3 custom tests** | Risk-driven testing |
| Prefect | One flow: `ingest(month)` → `dbt build` → log results. Retries, `month` parameter for backfill, monthly schedule | Orchestration, retries, parameterised reruns |
| Git + CI/CD | PR: lint, pytest, `dbt build` on fixture sample. `main`: build image → push to GHCR | Gated changes, versioned artifacts |
| Deploy | Docker Compose on homelab (Prefect server + worker + pipeline image), DuckDB on a volume. Pull-based updates via systemd timer | Something real runs on a schedule |

### Data scope
- Source: [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- **Yellow taxi only**, **2024-01 onward**, plus the taxi zone lookup CSV.

### Out of scope until after 2026-11-15
Dashboards · semantic layer / metrics · ML · green / FHV / HVFHV data · cloud deployment · data contract tooling · push-based deploy / self-hosted runner · Cloudflare Tunnel (separate homelab task)

Anything else → `docs/LATER.md`. Not built.

---

## 2. Ownership rules

1. **This charter is frozen.** New ideas, including AI suggestions, go to `docs/LATER.md` with one line on why. Nothing in `docs/LATER.md` gets built before 2026-11-15.
2. **No unexplained code merges.** If I can't explain a line, it doesn't go in.
3. **Every test justifies itself.** Before adding a test, write the failure it prevents in one line (in the test description or a comment). If I can't, the test is dropped.
4. **Weekly decision note.** End each week with a ~150-word note in `docs/decisions/` (template: `docs/decisions/0000-template.md`).

---

## 3. Architecture

```
            ┌──────────────── GitHub ────────────────┐
  PR   ──▶  │ GitHub-hosted runner                   │
            │   ruff · pytest · dbt build (fixture)  │
  main ──▶  │ build image → GHCR                     │
            │   tags: <commit-sha>, main             │
            └────────────────────────────────────────┘
                              │  (pull only — nothing inbound)
                              ▼
            ┌──────────────── Homelab ───────────────┐
            │ systemd timer (every 15 min)           │
            │   docker compose pull                  │
            │   if image changed: up -d + smoke flow │
            │                                        │
            │ Compose: prefect-server · worker ·     │
            │          pipeline image · duckdb volume│
            └────────────────────────────────────────┘

  Pipeline flow (Prefect):
  TLC Parquet ─▶ data/raw/ ─▶ validate ─▶ raw (DuckDB) ─▶ manifest
                              └─ fail ─▶ data/quarantine/
  raw ─▶ dbt: staging ─▶ intermediate ─▶ marts (≤3) + tests + freshness
```

### File layout (locked)
- `data/raw/` — downloaded source files only (monthly Parquet, zone lookup CSV)
- `data/quarantine/` — files that failed validation
- `<project-root>/*.duckdb` — the DuckDB warehouse
- `tests/` — committed test sample files used by pytest and CI
- `data/` and `*.duckdb` are gitignored; `tests/` sample files are committed

### Deployment decisions (locked)
- **Pull-based, automated.** The homelab pulls from GHCR on a timer. No manual SSH deploys, no self-hosted runner, no inbound exposure.
- **Image tags:** an immutable SHA tag per build plus a moving `main` tag. The homelab follows `main`.
- **Rollback:** pin a SHA in `.env`, then `docker compose up -d`.
- **Deploy script:** a small systemd timer + shell script, written by me, not Watchtower.
- **Done means it ran:** a deploy only counts if the smoke flow run succeeds and the result is logged. Prefect UI run history is the evidence.

---

## 4. Timeline

| Week | Dates | Done = merged to `main` |
|---|---|---|
| 1 | Oct 12–18 | Charter committed, repo scaffold, single-month ingestion + zone lookup |
| 2 | Oct 19–25 | **Walking skeleton:** CI → GHCR → homelab timer pulls + runs a dummy flow |
| 3 | Oct 26–Nov 1 | Manifest, idempotent reruns, backfill, load-time validation, pytest |
| 4 | Nov 2–8 | dbt staging / intermediate / marts, tests, source freshness |
| 5 | Nov 9–15 | Real Prefect flow + schedule, smoke test, README with architecture diagram |

**Checkpoint:** if the walking skeleton is not running on the homelab by **Oct 28**, stop and fix it before any further feature work.

### Cut order if behind (first cut first)
1. Third mart
2. Custom tests beyond 2
3. Prefect schedule (keep manual parameterised runs)
4. Fixture `dbt build` in CI (keep lint + pytest)

### Never cut
Ingestion · manifest · image build to GHCR · scheduled homelab run

---

## 5. Definition of done (2026-11-15)

- [ ] A fresh month can be ingested, re-run without duplicates, and backfilled by parameter
- [ ] A bad file is quarantined, not loaded
- [ ] `dbt build` passes with tests and freshness checks
- [ ] Merging to `main` produces a SHA-tagged image in GHCR with no manual steps
- [ ] The homelab picks up the new image automatically and the smoke flow succeeds
- [ ] README: problem, architecture diagram, how to run, key decisions
- [ ] Five weekly decision notes in `docs/decisions/`
