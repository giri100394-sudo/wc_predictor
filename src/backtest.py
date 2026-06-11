"""
Backtest the Poisson and Markov-chain models + EV optimizer against
held-out matches.

Trains each model on everything up to (but not including) --cutoff, then
walks forward through matches on/after --cutoff (default: friendlies,
since that's the bulk of pre-tournament fixtures) scoring the EV-optimal
scoreline pick against the actual result under the league's points rules.
A "most-likely scoreline" baseline is reported alongside it to show what
the EV optimizer buys you, and a comparison table is printed across
models.

Usage:
    python src/backtest.py
    python src/backtest.py --cutoff 2025-09-01 --tournament Friendly
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from poisson_model import PoissonModel
from markov_model import MarkovModel
from ev_optimizer import scoreline_evs
from tracker import score_prediction

ROOT = Path(__file__).resolve().parent.parent

GOAL_DIFF_BUCKETS = ["Draw", "1-goal", "2-3 goal", "4+ goal"]


def goal_diff_bucket(actual_a: int, actual_b: int) -> str:
    diff = abs(actual_a - actual_b)
    if diff == 0:
        return "Draw"
    if diff == 1:
        return "1-goal"
    if diff <= 3:
        return "2-3 goal"
    return "4+ goal"


def evaluate_model(model, test: pd.DataFrame) -> pd.DataFrame:
    """Run a fitted model (Poisson- or Markov-style, same interface) over
    the test set and return a per-match results DataFrame."""
    rows = []
    for _, m in test.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        mu_a, mu_b = model.expected_goals(a, b, neutral=neutral)
        grid = model.score_grid(a, b, neutral=neutral)
        evs = scoreline_evs(grid)

        ev_pick = evs[0]
        likely_pick = max(evs, key=lambda s: s.p_exact)

        actual_a, actual_b = int(m.home_score), int(m.away_score)
        ev_score = score_prediction(ev_pick.score_a, ev_pick.score_b,
                                      actual_a, actual_b, False)
        likely_score = score_prediction(likely_pick.score_a, likely_pick.score_b,
                                          actual_a, actual_b, False)

        actual_class = "A" if actual_a > actual_b else ("B" if actual_b > actual_a else "D")
        model_class = "A" if mu_a > mu_b else ("B" if mu_b > mu_a else "D")

        rows.append({
            "date": m.date.date(), "home": a, "away": b,
            "actual": f"{actual_a}-{actual_b}",
            "ev_pick": f"{ev_pick.score_a}-{ev_pick.score_b}",
            "ev_pts": ev_score["scoreline_points"],
            "ev_outcome": ev_score["outcome"],
            "likely_pick": f"{likely_pick.score_a}-{likely_pick.score_b}",
            "likely_pts": likely_score["scoreline_points"],
            "model_class": model_class,
            "actual_class": actual_class,
            "goal_diff_bucket": goal_diff_bucket(actual_a, actual_b),
        })
    return pd.DataFrame(rows)


def summarize(res: pd.DataFrame, label: str, pts_col: str, outcome_col: str | None = None) -> None:
    n = len(res)
    print(f"{label}:")
    print(f"  avg pts/match : {res[pts_col].mean():+.2f}  (max 5)")
    print(f"  total pts     : {res[pts_col].sum():+d} / {5 * n}")
    if outcome_col:
        vc = res[outcome_col].value_counts()
        for k in ["exact", "result", "wrong_winner", "wrong"]:
            print(f"  {k:<13}: {vc.get(k, 0)} ({vc.get(k, 0) / n:.0%})")
    print()


def bucket_rates(res: pd.DataFrame) -> pd.DataFrame:
    res = res.copy()
    res["goal_diff_bucket"] = pd.Categorical(
        res["goal_diff_bucket"], categories=GOAL_DIFF_BUCKETS, ordered=True)
    bucket = res.groupby("goal_diff_bucket", observed=True)
    return pd.DataFrame({
        "matches": bucket.size(),
        "avg_pts": bucket["ev_pts"].mean().round(2),
        "exact": bucket["ev_outcome"].apply(lambda s: (s == "exact").mean()),
        "result": bucket["ev_outcome"].apply(lambda s: (s == "result").mean()),
        "wrong_winner": bucket["ev_outcome"].apply(lambda s: (s == "wrong_winner").mean()),
    }).reindex(GOAL_DIFF_BUCKETS)


def report(res: pd.DataFrame, name: str, charts_dir: str | None) -> dict:
    """Print the full report for one model's results and return a row of
    headline numbers for the cross-model comparison table."""
    n = len(res)
    print(f"\n{'=' * 10} {name} {'=' * 10}")
    print(f"=== Backtest results ({n} matches) ===\n")
    summarize(res, "EV-optimal pick", "ev_pts", "ev_outcome")
    summarize(res, "Most-likely-scoreline baseline", "likely_pts")

    result_acc = (res["model_class"] == res["actual_class"]).mean()
    print(f"Result-direction accuracy (favorite called correctly): {result_acc:.0%}")

    avg_total_goals_actual = res["actual"].apply(
        lambda s: sum(int(x) for x in s.split("-"))).mean()
    avg_total_goals_pick = res["ev_pick"].apply(
        lambda s: sum(int(x) for x in s.split("-"))).mean()
    print(f"Avg total goals - actual: {avg_total_goals_actual:.2f}, "
          f"EV pick: {avg_total_goals_pick:.2f}")

    print("\nWorst EV picks (biggest miss):")
    print(res.sort_values("ev_pts").head(8)
          [["date", "home", "away", "actual", "ev_pick", "ev_pts"]]
          .to_string(index=False))

    rates = bucket_rates(res)
    print("\n=== EV-pick outcome rates by actual goal-difference bucket ===")
    printable = rates.copy()
    for col in ["exact", "result", "wrong_winner"]:
        printable[col] = (printable[col] * 100).round(0).astype("Int64").astype(str) + "%"
    print(printable.to_string())

    if charts_dir:
        make_charts(rates, charts_dir, prefix=name.lower() + "_")

    vc = res["ev_outcome"].value_counts()
    return {
        "model": name,
        "avg_pts": res["ev_pts"].mean(),
        "total_pts": res["ev_pts"].sum(),
        "exact_pct": vc.get("exact", 0) / n,
        "result_pct": vc.get("result", 0) / n,
        "wrong_winner_pct": vc.get("wrong_winner", 0) / n,
        "wrong_pct": vc.get("wrong", 0) / n,
        "result_acc": result_acc,
        "avg_total_goals_pick": avg_total_goals_pick,
    }


def main():
    ap = argparse.ArgumentParser(description="Backtest the prediction models")
    ap.add_argument("--matches", default=str(ROOT / "data" / "sample_matches.csv"))
    ap.add_argument("--cutoff", default="2026-01-01",
                    help="train on matches before this date, test on/after it")
    ap.add_argument("--tournament", default="Friendly",
                    help="tournament filter for the test set ('' = all)")
    ap.add_argument("--charts", default=None,
                    help="directory to write outcome-rate bar charts (requires matplotlib)")
    args = ap.parse_args()

    df = pd.read_csv(args.matches)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["home_score", "away_score"])

    cutoff = pd.Timestamp(args.cutoff)
    train_until = (cutoff - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Training on matches up to {train_until} ...")
    poisson = PoissonModel().fit(df, as_of=train_until)
    print(f"  Poisson : {len(poisson.attack)} teams, "
          f"home advantage {poisson.home_advantage:+.3f} (log-goals)")
    markov = MarkovModel().fit(df, as_of=train_until)
    print(f"  Markov  : {len(markov.pi)} teams, "
          f"home advantage {markov.home_advantage:+.3f} (goals), "
          f"sensitivity {markov.sensitivity:.3f}, rating scale {markov.rating_scale:.1f}")

    test = df[df["date"] >= cutoff]
    if args.tournament:
        test = test[test["tournament"] == args.tournament]
    # only teams both models have ratings for (new teams can't be predicted)
    known = set(poisson.attack) & set(markov.pi)
    test = test[test["home_team"].isin(known) & test["away_team"].isin(known)]
    print(f"Backtesting on {len(test)} matches from {args.cutoff} onward "
          f"(tournament={args.tournament or 'all'})")

    if len(test) == 0:
        print("No test matches found for that cutoff/tournament/team coverage.")
        return

    summary_rows = []
    for name, model in [("Poisson", poisson), ("Markov", markov)]:
        res = evaluate_model(model, test)
        summary_rows.append(report(res, name, args.charts))

    comparison = pd.DataFrame(summary_rows).set_index("model")
    print(f"\n{'=' * 10} Comparison ({len(test)} matches) {'=' * 10}")
    printable = comparison.copy()
    printable["avg_pts"] = printable["avg_pts"].map(lambda v: f"{v:+.2f}")
    printable["total_pts"] = printable["total_pts"].map(lambda v: f"{v:+.0f}")
    for col in ["exact_pct", "result_pct", "wrong_winner_pct", "wrong_pct", "result_acc"]:
        printable[col] = (printable[col] * 100).round(0).astype(int).astype(str) + "%"
    printable["avg_total_goals_pick"] = printable["avg_total_goals_pick"].map(lambda v: f"{v:.2f}")
    printable = printable.rename(columns={
        "avg_pts": "avg pts/match", "total_pts": "total pts",
        "exact_pct": "exact", "result_pct": "result",
        "wrong_winner_pct": "wrong winner", "wrong_pct": "wrong",
        "result_acc": "result-dir acc", "avg_total_goals_pick": "avg goals (pick)",
    })
    print(printable.to_string())


def make_charts(rates: pd.DataFrame, out_dir: str, prefix: str = "") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    charts = [
        ("exact", "Exact-scoreline rate by goal difference", f"{prefix}exact_rate.png"),
        ("result", "Correct-result rate by goal difference", f"{prefix}result_rate.png"),
        ("wrong_winner", "Wrong-winner rate by goal difference", f"{prefix}wrong_winner_rate.png"),
    ]
    for col, title, filename in charts:
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(rates.index.astype(str), rates[col] * 100,
                       color="#3DDC97" if col != "wrong_winner" else "#E07A5F")
        for b, v in zip(bars, rates[col] * 100):
            ax.annotate(f"{v:.0f}%", (b.get_x() + b.get_width() / 2, v),
                         ha="center", va="bottom")
        ax.set_title(title)
        ax.set_ylabel("% of matches")
        ax.set_ylim(0, max(rates[col].max() * 100 * 1.25, 10))
        fig.tight_layout()
        fig.savefig(out / filename, dpi=120)
        plt.close(fig)
    print(f"\nCharts written to {out}/ "
          f"({', '.join(f for _, _, f in charts)})")


if __name__ == "__main__":
    main()
