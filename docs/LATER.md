# LATER — parked ideas

Rule: anything outside `docs/CHARTER.md` lands here, one line each. **Nothing here is built before 2026-11-15.**
Review this list only after the definition of done is met.

| Date       | Idea                                                                                 | Source (me / AI) | Why it might matter                                                                                                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-10-09 | Green / FHV / HVFHV datasets                                                         | me               | Broader coverage, multi-source joins                                                                                                                                                                         |
| 2026-10-09 | Push-based deploy via Cloudflare Tunnel                                              | me               | Instant deploys, deploy status in GitHub                                                                                                                                                                     |
| 2026-10-09 | Dashboard on top of marts                                                            | me               | Visual demo for non-technical reviewers                                                                                                                                                                      |
| 2026-10-10 | Raw layer as DuckDB views over monthly Parquet files instead of a loaded `raw` table | me               | Reruns/backfill become file replacement; no duplicate storage in DuckDB. <br>Trade-offs: loses load-time typing, `_loaded_at`/`_file_sha256` columns, and makes any bad file in `data/raw/` live immediately |
