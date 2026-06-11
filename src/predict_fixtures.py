"""
Export an Excel workbook with two sheets:

  1. "Friendlies vs actual" - completed friendlies from --friendly-from,
     with the actual result alongside each model's most-likely-scoreline
     prediction (models trained out-of-sample, on data before that window).
  2. "World Cup predictions" - upcoming (unplayed) World Cup fixtures from
     --wc-from, with each model's most-likely-scoreline prediction (models
     trained on all available data).

Usage:
    python src/predict_fixtures.py
    python src/predict_fixtures.py --xlsx data/predictions.xlsx
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from poisson_model import PoissonModel
from markov_model import MarkovModel
from tracker import score_prediction

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


def build_table(poisson: PoissonModel, markov: MarkovModel,
                fixtures: pd.DataFrame, actual: bool) -> pd.DataFrame:
    rows = []
    for _, m in fixtures.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        row = {
            "Date": m.date.date(),
            "Home": a,
            "Away": b,
            "Venue": "Neutral" if neutral else f"{a} (host)",
        }
        if actual:
            actual_a, actual_b = int(m.home_score), int(m.away_score)
            row["Actual"] = f"{actual_a}-{actual_b}"
            row["Actual result"] = outcome(actual_a, actual_b)

        for name, model in [("Poisson", poisson), ("Markov", markov)]:
            grid = model.score_grid(a, b, neutral=neutral)
            i, j, p = most_likely(grid)
            row[f"{name} pred"] = f"{i}-{j}"
            row[f"{name} result"] = outcome(i, j)
            row[f"{name} P(exact)"] = round(p, 2)
            if actual:
                sc = score_prediction(i, j, actual_a, actual_b, False)
                row[f"{name} hit"] = sc["outcome"]
                row[f"{name} pts"] = sc["scoreline_points"]
        rows.append(row)
    return pd.DataFrame(rows)


def autofit(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    ws = writer.sheets[sheet_name]
    for col_idx, col in enumerate(df.columns, start=1):
        width = max(len(str(col)), df[col].astype(str).map(len).max() if len(df) else 0) + 2
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = min(width, 28)


def main():
    ap = argparse.ArgumentParser(description="Export Poisson/Markov predictions to Excel")
    ap.add_argument("--matches", default=str(ROOT / "data" / "sample_matches.csv"))
    ap.add_argument("--friendly-from", default="2026-06-01",
                    help="completed-friendlies sheet starts here")
    ap.add_argument("--friendly-tournament", default="Friendly",
                    help="tournament filter for the friendlies sheet ('' = all)")
    ap.add_argument("--wc-from", default="2026-06-11",
                    help="World Cup predictions sheet starts here")
    ap.add_argument("--wc-tournament", default="FIFA World Cup",
                    help="tournament filter for the World Cup sheet ('' = all)")
    ap.add_argument("--xlsx", default=str(ROOT / "data" / "predictions.xlsx"))
    args = ap.parse_args()

    df = pd.read_csv(args.matches)
    df["date"] = pd.to_datetime(df["date"])

    # historical models: out-of-sample as of the day before the friendly window
    train_until = (pd.Timestamp(args.friendly_from) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    poisson_hist = PoissonModel().fit(df, as_of=train_until)
    markov_hist = MarkovModel().fit(df, as_of=train_until)

    # current models: trained on all available results
    poisson_now = PoissonModel().fit(df)
    markov_now = MarkovModel().fit(df)

    known_hist = set(poisson_hist.attack) & set(markov_hist.pi)
    known_now = set(poisson_now.attack) & set(markov_now.pi)

    friendlies = df.dropna(subset=["home_score", "away_score"])
    friendlies = friendlies[friendlies["date"] >= args.friendly_from]
    if args.friendly_tournament:
        friendlies = friendlies[friendlies["tournament"] == args.friendly_tournament]
    friendlies = friendlies[friendlies["home_team"].isin(known_hist)
                             & friendlies["away_team"].isin(known_hist)]
    friendlies = friendlies.sort_values("date")

    wc = df[df["home_score"].isna()]
    wc = wc[wc["date"] >= args.wc_from]
    if args.wc_tournament:
        wc = wc[wc["tournament"] == args.wc_tournament]
    wc = wc[wc["home_team"].isin(known_now) & wc["away_team"].isin(known_now)]
    wc = wc.sort_values("date")

    friendlies_table = build_table(poisson_hist, markov_hist, friendlies, actual=True)
    wc_table = build_table(poisson_now, markov_now, wc, actual=False)

    with pd.ExcelWriter(args.xlsx, engine="openpyxl") as writer:
        friendlies_table.to_excel(writer, sheet_name="Friendlies vs actual", index=False)
        wc_table.to_excel(writer, sheet_name="World Cup predictions", index=False)
        autofit(writer, "Friendlies vs actual", friendlies_table)
        autofit(writer, "World Cup predictions", wc_table)

    print(f"Friendlies vs actual : {len(friendlies_table)} matches "
          f"(from {args.friendly_from}, tournament={args.friendly_tournament or 'all'}, "
          f"models trained through {train_until})")
    print(f"World Cup predictions: {len(wc_table)} fixtures "
          f"(from {args.wc_from}, tournament={args.wc_tournament or 'all'}, "
          f"models trained on all available results)")
    print(f"Wrote {args.xlsx}")


if __name__ == "__main__":
    main()
