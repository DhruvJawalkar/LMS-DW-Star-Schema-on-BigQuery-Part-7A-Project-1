# CLAUDE.md — Project 1: Building the LMS Star Schema on BigQuery

**Companion to:** Part 7A — Data Warehousing & ETL
**Companion PDF:** `Part7A_Project1_LMS_Star_Schema_BigQuery.pdf` (full DDL, SQL, and conceptual walkthrough — this file is the *execution* plan; the PDF is the *reference*)
**Repo:** `github.com/DhruvJawalkar/LMS-Microservices-Part-7A-Project-1`

## Goal

Build a working Kimball-style star schema for the LMS on BigQuery: `lending_fact`,
`reservation_fact`, and conformed `book_dim` (SCD Type 2), `member_dim`, `branch_dim`,
`date_dim`. Demonstrate partitioning/clustering performance gains, SCD Type 2 history,
and validate against the Section 5 quarter-over-quarter query. Work phase by phase —
do not skip ahead. Stop and report status at the end of each phase before continuing.

---

## Repo Structure to Create

```
LMS-Microservices-Part-7A-Project-1/
├── README.md
├── data/
│   └── generate_synthetic_data.py
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
└── RESULTS.md          <- written at the end, captures actual numbers/output
```

---

## Phase 0: Environment Setup

**Do:**
1. Confirm `gcloud` CLI is authenticated and a GCP project is set (`gcloud config list`).
2. Confirm the BigQuery API is enabled on the target project.
3. Confirm `bq` CLI works: `bq ls` should return without error (empty list is fine).

**File checklist:** none yet — this phase is verification only.

**Verify before continuing:**
- [ ] `gcloud config list` shows an active project
- [ ] `bq ls` runs without an auth/permission error

Report the project ID being used before moving to Phase 1.

---

## Phase 1: Synthetic Data Generation

**Do:**
Write `data/generate_synthetic_data.py` to produce CSVs for:
- `books.csv` — ~5,000 synthetic books, with `book_id`, `title`, `category` (drawn from
  a realistic category list: Fiction, Young Adult, Reference, Children's Fiction,
  Mystery, Sci-Fi), `publisher_name`
- `members.csv` — ~2,000 synthetic members
- `branches.csv` — ~15 synthetic branches with region assignment
- `lending_events.csv` — ~500,000 synthetic lending events spanning 3 years
  (2023-01-01 through 2026-03-31), each referencing a valid book/member/branch,
  with a realistic non-uniform date distribution (more recent months should have
  more volume, to make the partitioning demo in Phase 4 meaningful)
- `reservation_events.csv` — ~100,000 synthetic reservation events, same span

Use `faker` or simple randomized generation — realism of names doesn't matter,
**referential integrity and realistic date distribution do**. Every foreign key
in lending/reservation events must reference a row that actually exists in the
corresponding dimension CSV.

**File checklist:**
- [ ] `data/generate_synthetic_data.py` exists and runs without error
- [ ] `data/books.csv`, `data/members.csv`, `data/branches.csv`,
      `data/lending_events.csv`, `data/reservation_events.csv` all generated

**Verify before continuing:**
- [ ] Row counts roughly match targets above (print counts at end of script)
- [ ] Spot-check: every `book_id` in `lending_events.csv` exists in `books.csv`
      (write a quick assertion in the script itself, don't skip this)

---

## Phase 2: Schema & Table Creation

**Do:**
Create `sql/01_create_schema_and_dims.sql` (schema + `date_dim`, `branch_dim`,
`member_dim`), `sql/02_create_book_dim.sql` (SCD Type 2 shape), and
`sql/03_create_fact_tables.sql` (`lending_fact`, `reservation_fact`) using the exact
DDL from the companion PDF's Phase 1 / Appendix. Run all three against BigQuery via
`bq query` or the `bq` DDL execution path.

**File checklist:**
- [ ] `sql/01_create_schema_and_dims.sql`
- [ ] `sql/02_create_book_dim.sql`
- [ ] `sql/03_create_fact_tables.sql`

**Verify before continuing:**
- [ ] `bq ls lms_warehouse` shows all 5 base tables
- [ ] `bq show lms_warehouse.book_dim` confirms the SCD Type 2 columns
      (`effective_start_date`, `effective_end_date`, `is_current`) are present

---

## Phase 3: Load Synthetic Data

**Do:**
Write `scripts/load_data.sh` to load each CSV into its corresponding base table via
`bq load`. Populate `book_dim` with `is_current = TRUE`, `effective_start_date` =
an arbitrary backdated date, `effective_end_date = NULL` for every row (this is the
"initial load" state — the Phase 5 SCD walkthrough will create the first real
history event on top of this).

**File checklist:**
- [ ] `scripts/load_data.sh`

**Verify before continuing:**
- [ ] `SELECT COUNT(*) FROM lms_warehouse.lending_fact` matches the generated row
      count from Phase 1
- [ ] No load errors/rejected rows (check `bq load` job output)

---

## Phase 4: Partitioning, Clustering & Performance Comparison

**Do:**
Run `sql/04_create_optimized_lending_fact.sql` (from the companion PDF's Phase 2)
to create `lending_fact_optimized`. Write `scripts/dry_run_comparison.sh` that runs
the same date-filtered aggregation query as a dry-run (`bq query --dry_run`) against
both `lending_fact` and `lending_fact_optimized`, and prints the bytes-processed
figure for each.

**File checklist:**
- [ ] `sql/04_create_optimized_lending_fact.sql`
- [ ] `scripts/dry_run_comparison.sh`

**Verify before continuing:**
- [ ] Script output clearly shows both byte counts side by side
- [ ] The optimized table's byte count is meaningfully lower than the naive table's
      for a narrow date-range query (record both numbers — they go in `RESULTS.md`)

---

## Phase 5: SCD Type 2 Walkthrough

**Do:**
Write `sql/05_scd_type2_update.sql` implementing the exact two-step SCD Type 2
update from the companion PDF's Phase 3, against one real book from the loaded
synthetic data (pick any `book_id` that has existing lending events, so the
"pre- and post-reclassification" verification query in the PDF has data to prove
the point against). Run it, then run the verification query from the PDF confirming
both versions are independently queryable.

**File checklist:**
- [ ] `sql/05_scd_type2_update.sql`

**Verify before continuing:**
- [ ] The verification query for the pre-reclassification surrogate key returns the
      original category
- [ ] The verification query for the post-reclassification surrogate key returns the
      new category
- [ ] `SELECT COUNT(*) FROM lms_warehouse.book_dim WHERE book_id = '<the test book_id>'`
      returns 2 (one expired row, one current row) — if it returns 1, the SCD logic
      didn't insert correctly; if it returns more than 2, something ran twice

---

## Phase 6: Validation Query

**Do:**
Write `sql/06_validation_queries.sql` with the exact Section 5 quarter-over-quarter
query from the companion PDF's Phase 4, run against `lending_fact_optimized`.

**File checklist:**
- [ ] `sql/06_validation_queries.sql`

**Verify before continuing:**
- [ ] Query runs without error and returns rows grouped by category, branch, and quarter
- [ ] Spot-check one row's `total_lendings` count against a manual `COUNT(*)` filtered
      to the same category/branch/quarter, to confirm the aggregation is correct

---

## Phase 7: Wrap-Up

**Do:**
Write `RESULTS.md` summarizing: final row counts per table, the Phase 4 byte-comparison
numbers, confirmation that the Phase 5 and Phase 6 verification checks passed, and
any deviations from this plan (and why) made during implementation. Write `README.md`
with setup/run instructions for someone else to reproduce this project from scratch.

**File checklist:**
- [ ] `RESULTS.md`
- [ ] `README.md`

**Final verification (all should be true before calling this project done):**
- [ ] Every phase's checklist above is checked off
- [ ] `RESULTS.md` contains actual numbers, not placeholders
- [ ] Re-running `scripts/load_data.sh` and `sql/05_scd_type2_update.sql` from a clean
      dataset reproduces the same verification results (confirms nothing was a
      one-off manual fix)
