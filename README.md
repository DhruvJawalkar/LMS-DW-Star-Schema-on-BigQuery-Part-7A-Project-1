# LMS Star Schema on BigQuery — Part 7A, Project 1

Companion project to **Part 7A — Data Warehousing & ETL** of *Developing Intuition on
Building Blocks — for Systems Design*. Builds a working Kimball-style star schema for
a Library Management System (LMS) on BigQuery: `lending_fact`, `reservation_fact`, and
conformed `book_dim` (SCD Type 2), `member_dim`, `branch_dim`, `date_dim`.

Full DDL, SQL, and conceptual walkthrough live in
[`Part7A_Project1_LMS_Star_Schema_BigQuery.pdf`](./Part7A_Project1_LMS_Star_Schema_BigQuery.pdf).
[`CLAUDE.md`](./CLAUDE.md) is the phase-by-phase execution plan this repo follows.

## What this project demonstrates

- A Kimball star schema on BigQuery, sized for realistic query patterns
- **SCD Type 2** history on `book_dim.category`, with pre- and post-reclassification
  rows independently queryable against the correct lending events
- **Partitioning + clustering** on the fact tables (`PARTITION BY` month on
  `lending_date`, `CLUSTER BY branch_key, book_key`), with a measured before/after
  bytes-processed comparison on a date-filtered query
- The exact quarter-over-quarter lending-trend query used elsewhere in the article to
  compare Inmon, Kimball, and Data Vault architectures, run and validated against real
  (synthetic) data

## Repo structure

```
├── CLAUDE.md                                    # phased execution plan
├── Part7A_Project1_LMS_Star_Schema_BigQuery.pdf # DDL / SQL reference
├── data/
│   └── generate_synthetic_data.py               # synthetic CSV generator
├── sql/
│   ├── 01_create_schema_and_dims.sql
│   ├── 02_create_book_dim.sql
│   ├── 03_create_fact_tables.sql
│   ├── 04_create_optimized_lending_fact.sql
│   ├── 05_scd_type2_update.sql
│   └── 06_validation_queries.sql
├── scripts/
│   ├── load_data.sh
│   └── dry_run_comparison.sh
└── RESULTS.md                                    # actual numbers, written at the end
```

## Project status

This project is implemented phase by phase, per `CLAUDE.md`. Current status:

| Phase | Description | Status |
|---|---|---|
| 0 | Environment setup (`gcloud`/`bq` auth) | Skipped for now — set up separately before Phase 2 |
| 1 | Synthetic data generation | **Done** |
| 2 | Schema & table creation (BigQuery DDL) | Pending |
| 3 | Load synthetic data | Pending |
| 4 | Partitioning, clustering & performance comparison | Pending |
| 5 | SCD Type 2 walkthrough | Pending |
| 6 | Validation query | Pending |
| 7 | Wrap-up (`RESULTS.md`) | Pending |

## How to run

### Phase 1 — generate synthetic data

Requires Python 3 with `numpy`, `pandas`, and `faker`:

```bash
pip install numpy pandas faker
python data/generate_synthetic_data.py
```

This writes five CSVs into `data/` (git-ignored — regenerate locally rather than
pulling from git history):

| File | Rows | Notes |
|---|---|---|
| `books.csv` | ~5,000 | `book_id`, `title`, `category`, `publisher_name` |
| `members.csv` | ~2,000 | `member_id`, `member_name`, `home_branch_id` |
| `branches.csv` | ~15 | `branch_id`, `branch_name`, `region` |
| `lending_events.csv` | ~500,000 | 2023-01-01 → 2026-03-31, volume skewed toward recent months |
| `reservation_events.csv` | ~100,000 | same span |

The generator uses a fixed random seed (`42`), so re-running it reproduces the same
data. All foreign keys in the event CSVs are sampled directly from the generated
dimension arrays, so referential integrity is guaranteed by construction; the script
asserts this before printing row counts.

### Phases 0, 2–7

Not yet implemented in this repo. Once added, this section will be updated with:

- Phase 0: `gcloud config list` / `bq ls` verification steps
- Phase 2: running the `sql/01`–`03` DDL scripts against BigQuery via `bq query`
- Phase 3: `scripts/load_data.sh` to load the Phase 1 CSVs into the base tables
- Phase 4: `scripts/dry_run_comparison.sh` to compare bytes-processed between the
  naive and partitioned/clustered `lending_fact` tables
- Phase 5: running `sql/05_scd_type2_update.sql` and its verification queries
- Phase 6: running `sql/06_validation_queries.sql`
- Phase 7: see `RESULTS.md` for actual numbers once the full pipeline has run

## Outcomes

Once all phases are complete, `RESULTS.md` will capture:

- Final row counts per table (post-load)
- Actual dry-run bytes-processed for the naive vs. partitioned/clustered
  `lending_fact` query, and the relative improvement
- Confirmation that the SCD Type 2 pre/post-reclassification verification queries
  passed, and that `book_dim` shows exactly 2 rows for the test `book_id`
- Confirmation that the Section 5 quarter-over-quarter validation query returns
  correct, spot-checked results

Until then, this README reflects the plan and the current (Phase 1) implementation
state — see the status table above.
