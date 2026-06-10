"""
CLI: predict a match under the league's points system.

Usage:
    python src/predict.py "France" "England"
    python src/predict.py "USA" "Mexico" --host USA      # host gets home advantage
    python src/predict.py "Spain" "Brazil" --matches data/my_real_results.csv
"""

import argparse
from pathlib import Path

import pandas as pd

from poisson_model import PoissonModel
from ev_optimizer import best_prediction, scoreline_evs

ROOT = Path(__file__).resolve().parent.parent


def load_players(path: Path, team: str) -> list[dict]:
    df = pd.read_csv(path)
    return df[df["team"] == team].to_dict("records")


def main():
    ap = argparse.ArgumentParser(description="World Cup prediction-league optimizer")
    ap.add_argument("team_a")
    ap.add_argument("team_b")
    ap.add_argument("--matches", default=str(ROOT / "data" / "sample_matches.csv"))
    ap.add_argument("--players", default=str(ROOT / "data" / "sample_players.csv"))
    ap.add_argument("--host", default=None,
                    help="team name if one side has true home advantage")
    args = ap.parse_args()

    model = PoissonModel().fit(pd.read_csv(args.matches))

    neutral = args.host is None
    a, b = args.team_a, args.team_b
    if args.host == b:           # model gives home adv to team_a slot
        a, b = b, a

    mu_a, mu_b = model.expected_goals(a, b, neutral=neutral)
    grid = model.score_grid(a, b, neutral=neutral)

    players_a = load_players(Path(args.players), a)
    players_b = load_players(Path(args.players), b)
    rec = best_prediction(grid, mu_a, mu_b, players_a, players_b)

    s = rec["scoreline"]
    print(f"\n=== {a} vs {b} {'(neutral)' if neutral else f'(host: {a})'} ===")
    print(f"Expected goals:  {a} {mu_a:.2f} — {mu_b:.2f} {b}")

    import numpy as np
    p_a = float(np.tril(grid, -1).sum())
    p_d = float(np.trace(grid))
    p_b = float(np.triu(grid, 1).sum())
    print(f"Result odds:     {a} {p_a:.0%} | draw {p_d:.0%} | {b} {p_b:.0%}\n")

    print(f">>> RECOMMENDED PREDICTION: {a} {s.score_a}–{s.score_b} {b}")
    print(f"    EV {s.ev:+.2f} pts   "
          f"(exact {s.p_exact:.1%} ×5 | result {s.p_result:.1%} ×3 | "
          f"wrong-winner risk {s.p_opposite_win:.1%} ×−2)")
    if rec["scorer"]:
        sc = rec["scorer"]
        print(f">>> RECOMMENDED SCORER:     {sc.player} ({sc.team})  "
              f"P(scores) {sc.p_scores:.1%}  EV {sc.ev:+.2f}")
    print(f">>> TOTAL EXPECTED POINTS:  {rec['expected_points']:.2f} / 7\n")

    print("Scoreline alternatives:")
    for alt in rec["scoreline_alternatives"]:
        tag = "draw — no penalty risk" if alt.score_a == alt.score_b else ""
        print(f"  {alt.score_a}–{alt.score_b}  EV {alt.ev:+.2f}  "
              f"(exact {alt.p_exact:.1%})  {tag}")

    if rec["scorer_alternatives"]:
        print("\nScorer alternatives:")
        for alt in rec["scorer_alternatives"]:
            print(f"  {alt.player:<22} ({alt.team})  P(scores) {alt.p_scores:.1%}")


if __name__ == "__main__":
    main()
