# 0002 — Zone lookup load semantics

**Week:** 1  **Date:** 2026-10-13

## Context
Trip records identify pickup and drop-off locations only by `PULocationID` and `DOLocationID`. The TLC taxi zone lookup (~265 rows) maps those IDs to borough and zone names, and the Week 4 marts need it for labelling. It is static reference data, not tied to a month.

## Decision
- Reload the zone file in full (`CREATE OR REPLACE TABLE`) on every run, after the trips load.
- Read every column as `VARCHAR` (`all_varchar=true`), then `CAST` explicitly using `schema.RAW_TAXI_ZONE_LOOKUP_COLUMNS`.
- Trade-off: each run overwrites the previous version of the file and the table. Versioning is parked in `docs/LATER.md`.

## Alternatives considered
- A `--refresh-zones` flag — on a fresh warehouse (Docker volume, CI) the table would not exist until someone remembered the flag, and the dbt join would break.
- Load zones before trips — the two raw loads are independent, so a zone failure would block trip ingestion for no benefit.
- DuckDB type sniffing — the types would no longer be under my control. In practice the sniffer typed `LocationID` as `BIGINT` while `PULocationID` is `INTEGER`, and a single non-numeric value would silently turn a whole column into `VARCHAR`.

## Plain-language explanation
The zone lookup is reloaded in full on every run, after the trips. Loading it every time means a fresh warehouse always has the table, and because the two loads are independent, a zone failure never blocks the trip data. Instead of letting DuckDB guess the column types, I read every column as text and cast each one to the type I chose. The explicit column list fails loudly if a column is renamed or removed, and the cast fails loudly if a value doesn't fit its type. A newly added column, however, is silently ignored. Because the table is replaced on every run, the previous version is overwritten and its history is lost. I accept that for now; the fix is parked in `docs/LATER.md`.

## What would make me revisit this
TLC relabels or renumbers zones, or adds a column the marts need.
