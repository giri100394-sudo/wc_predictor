"""
Predict the most-likely scoreline for upcoming (unplayed) fixtures using
both the Poisson and Markov-chain models.

Usage:
    python src/predict_fixtures.py
    python src/predict_fixtures.py --tournament "FIFA World Cup" --from-date 2026-06-11
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from poisson_model import PoissonModel
from markov_model import MarkovModel

ROOT = Path(__file__).resolve().parent.parent


def most_likely(grid: np.ndarray) -> tuple[int, int, float]:
    i, j = np.unravel_index(np.argmax(grid), grid.shape)
    return int(i), int(j), float(grid[i, j])


def outcome(score_a: int, score_b: int) -> str:
    if score_a > score_b:
        return "1"
    if score_a < score_b:
        return "2"
    return "X"


def main():
    ap = argparse.ArgumentParser(description="Predict upcoming fixtures")
    ap.add_argument("--matches", default=str(ROOT / "data" / "sample_matches.csv"))
    ap.add_argument("--tournament", default="FIFA World Cup",
                    help="tournament filter ('' = all)")
    ap.add_argument("--from-date", dest="from_date", default=None,
                    help="only fixtures on/after this date")
    ap.add_argument("--out", default=None,
                    help="write CSV to this path (UTF-8) instead of stdout")
    args = ap.parse_args()

    df = pd.read_csv(args.matches)
    df["date"] = pd.to_datetime(df["date"])

    poisson = PoissonModel().fit(df)
    markov = MarkovModel().fit(df)

    fixtures = df[df["home_score"].isna()]
    if args.tournament:
        fixtures = fixtures[fixtures["tournament"] == args.tournament]
    if args.from_date:
        fixtures = fixtures[fixtures["date"] >= pd.Timestamp(args.from_date)]
    fixtures = fixtures.sort_values("date")

    known = set(poisson.attack) & set(markov.pi)
    fixtures = fixtures[fixtures["home_team"].isin(known) & fixtures["away_team"].isin(known)]

    rows = []
    for _, m in fixtures.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        row = {
            "Date": m.date.date(),
            "Home": a,
            "Away": b,
            "Venue": "Neutral" if neutral else f"{a} (host)",
        }
        for name, model in [("Poisson", poisson), ("Markov", markov)]:
            grid = model.score_grid(a, b, neutral=neutral)
            i, j, p = most_likely(grid)
            row[f"{name} score"] = f"{i}-{j}"
            row[f"{name} result"] = outcome(i, j)
            row[f"{name} P(exact)"] = f"{p:.0%}"
        rows.append(row)

    res = pd.DataFrame(rows)
    if args.out:
        res.to_csv(args.out, sep=",", index=False, encoding="utf-8")
        print(f"Wrote {len(res)} fixtures to {args.out}")
    else:
        print(res.to_csv(sep="\t", index=False))


if __name__ == "__main__":
    main()
