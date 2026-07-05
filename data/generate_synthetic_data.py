"""
Generates synthetic LMS operational CSVs for Project 1 (Part 7A).

Requires: numpy, pandas, faker (pip install numpy pandas faker)

Output (written to this script's directory):
    books.csv               ~5,000 rows
    members.csv              ~2,000 rows
    branches.csv                 ~15 rows
    lending_events.csv        ~500,000 rows (2023-01-01 .. 2026-03-31)
    reservation_events.csv    ~100,000 rows (2023-01-01 .. 2026-03-31)

Referential integrity is enforced by construction: lending/reservation events
sample their book_id/member_id/branch_id from the actual generated dimension
arrays, never from independently generated values. Assertions at the bottom
double-check this before the script reports success.
"""

import calendar
import os

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

N_BOOKS = 5_000
N_MEMBERS = 2_000
N_BRANCHES = 15
N_LENDING_EVENTS = 500_000
N_RESERVATION_EVENTS = 100_000

CATEGORIES = [
    "Fiction",
    "Young Adult",
    "Reference",
    "Children's Fiction",
    "Mystery",
    "Sci-Fi",
]
REGIONS = ["North", "South", "East", "West", "Central"]

# Event date span, inclusive.
SPAN_START = (2023, 1)
SPAN_END = (2026, 3)

rng = np.random.default_rng(SEED)
fake = Faker()
Faker.seed(SEED)


def month_range(start, end):
    """List of (year, month) tuples from start to end, inclusive."""
    y, m = start
    months = []
    while (y, m) <= end:
        months.append((y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return months


def sample_event_dates(n):
    """
    Vectorized sampling of `n` dates across MONTHS, weighted so more recent
    months get more volume (later month index -> higher weight).
    """
    months = month_range(SPAN_START, SPAN_END)
    n_months = len(months)

    # Linearly increasing weight: earliest month weight 1, latest month weight n_months.
    weights = np.arange(1, n_months + 1, dtype=np.float64)
    weights /= weights.sum()

    month_idx = rng.choice(n_months, size=n, p=weights)

    years = np.array([months[i][0] for i in range(n_months)])[month_idx]
    mons = np.array([months[i][1] for i in range(n_months)])[month_idx]
    days_in_month = np.array(
        [calendar.monthrange(y, m)[1] for (y, m) in months]
    )[month_idx]

    day_offset = rng.integers(0, days_in_month)
    days = day_offset + 1

    dates = pd.to_datetime(
        {"year": years, "month": mons, "day": days}
    )
    return dates


def generate_branches():
    branch_ids = [f"BR-{i + 1:03d}" for i in range(N_BRANCHES)]
    branch_names = [f"{fake.city()} Branch" for _ in range(N_BRANCHES)]
    regions = rng.choice(REGIONS, size=N_BRANCHES)
    df = pd.DataFrame(
        {
            "branch_id": branch_ids,
            "branch_name": branch_names,
            "region": regions,
        }
    )
    df.to_csv(os.path.join(OUT_DIR, "branches.csv"), index=False)
    return df


def generate_members(branch_ids):
    member_ids = [f"M-{i + 1:05d}" for i in range(N_MEMBERS)]
    member_names = [fake.name() for _ in range(N_MEMBERS)]
    home_branch_id = rng.choice(branch_ids, size=N_MEMBERS)
    df = pd.DataFrame(
        {
            "member_id": member_ids,
            "member_name": member_names,
            "home_branch_id": home_branch_id,
        }
    )
    df.to_csv(os.path.join(OUT_DIR, "members.csv"), index=False)
    return df


def generate_books():
    book_ids = [f"B-{i + 1:05d}" for i in range(N_BOOKS)]
    titles = [fake.catch_phrase() for _ in range(N_BOOKS)]
    category = rng.choice(CATEGORIES, size=N_BOOKS)
    # A conformed pool of ~40 publishers looks more realistic than fully
    # unique company names per book.
    publisher_pool = [fake.company() for _ in range(40)]
    publisher_name = rng.choice(publisher_pool, size=N_BOOKS)
    df = pd.DataFrame(
        {
            "book_id": book_ids,
            "title": titles,
            "category": category,
            "publisher_name": publisher_name,
        }
    )
    df.to_csv(os.path.join(OUT_DIR, "books.csv"), index=False)
    return df


def generate_lending_events(book_ids, member_ids, branch_ids):
    n = N_LENDING_EVENTS
    lending_ids = [f"L-{i + 1:07d}" for i in range(n)]
    book_id = rng.choice(book_ids, size=n)
    member_id = rng.choice(member_ids, size=n)
    branch_id = rng.choice(branch_ids, size=n)
    lending_date = sample_event_dates(n)
    loan_duration_days = rng.choice([7, 14, 21, 30], size=n, p=[0.35, 0.35, 0.2, 0.1])

    has_fine = rng.random(n) < 0.12
    fine_amount = np.where(
        has_fine, np.round(rng.uniform(0.25, 15.00, size=n), 2), 0.00
    )

    df = pd.DataFrame(
        {
            "lending_id": lending_ids,
            "book_id": book_id,
            "member_id": member_id,
            "branch_id": branch_id,
            "lending_date": lending_date.dt.strftime("%Y-%m-%d"),
            "loan_duration_days": loan_duration_days,
            "fine_amount": fine_amount,
        }
    )
    df.to_csv(os.path.join(OUT_DIR, "lending_events.csv"), index=False)
    return df


def generate_reservation_events(book_ids, member_ids, branch_ids):
    n = N_RESERVATION_EVENTS
    reservation_ids = [f"R-{i + 1:07d}" for i in range(n)]
    book_id = rng.choice(book_ids, size=n)
    member_id = rng.choice(member_ids, size=n)
    branch_id = rng.choice(branch_ids, size=n)
    reservation_date = sample_event_dates(n)
    time_to_fulfillment_hours = rng.integers(1, 337, size=n)  # up to ~2 weeks
    is_cancelled = rng.random(n) < 0.12

    df = pd.DataFrame(
        {
            "reservation_id": reservation_ids,
            "book_id": book_id,
            "member_id": member_id,
            "branch_id": branch_id,
            "reservation_date": reservation_date.dt.strftime("%Y-%m-%d"),
            "time_to_fulfillment_hours": time_to_fulfillment_hours,
            "is_cancelled": is_cancelled,
        }
    )
    df.to_csv(os.path.join(OUT_DIR, "reservation_events.csv"), index=False)
    return df


def main():
    branches_df = generate_branches()
    members_df = generate_members(branches_df["branch_id"].values)
    books_df = generate_books()
    lending_df = generate_lending_events(
        books_df["book_id"].values,
        members_df["member_id"].values,
        branches_df["branch_id"].values,
    )
    reservation_df = generate_reservation_events(
        books_df["book_id"].values,
        members_df["member_id"].values,
        branches_df["branch_id"].values,
    )

    # Referential integrity assertions -- do not skip.
    assert set(lending_df["book_id"]).issubset(set(books_df["book_id"]))
    assert set(lending_df["member_id"]).issubset(set(members_df["member_id"]))
    assert set(lending_df["branch_id"]).issubset(set(branches_df["branch_id"]))
    assert set(reservation_df["book_id"]).issubset(set(books_df["book_id"]))
    assert set(reservation_df["member_id"]).issubset(set(members_df["member_id"]))
    assert set(reservation_df["branch_id"]).issubset(set(branches_df["branch_id"]))

    min_date = min(lending_df["lending_date"].min(), reservation_df["reservation_date"].min())
    max_date = max(lending_df["lending_date"].max(), reservation_df["reservation_date"].max())

    print("Synthetic data generation complete.")
    print(f"  branches.csv:            {len(branches_df):>8,} rows")
    print(f"  members.csv:             {len(members_df):>8,} rows")
    print(f"  books.csv:               {len(books_df):>8,} rows")
    print(f"  lending_events.csv:      {len(lending_df):>8,} rows")
    print(f"  reservation_events.csv:  {len(reservation_df):>8,} rows")
    print(f"  event date range:        {min_date} .. {max_date}")
    print("  referential integrity assertions: PASSED")


if __name__ == "__main__":
    main()
