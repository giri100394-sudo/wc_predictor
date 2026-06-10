"""
Generates sample historical match data calibrated to rough real-world team
strengths. The output format matches the popular Kaggle "International
football results" dataset (results.csv), so you can swap in the real thing
with zero code changes:

    https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017

Columns: date, home_team, away_team, home_score, away_score, tournament, neutral
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# Rough relative strengths (attack, defense) on a goals-per-game scale.
# attack: expected goals scored vs an average side
# defense: multiplier on opponent's expected goals (lower = better)
TEAM_STRENGTH = {
    "Argentina":     (2.10, 0.65),
    "France":        (2.05, 0.70),
    "Spain":         (2.10, 0.70),
    "England":       (1.95, 0.70),
    "Brazil":        (1.95, 0.75),
    "Portugal":      (1.90, 0.75),
    "Germany":       (1.85, 0.85),
    "Netherlands":   (1.80, 0.80),
    "Belgium":       (1.70, 0.90),
    "Italy":         (1.60, 0.75),
    "Uruguay":       (1.60, 0.80),
    "Croatia":       (1.55, 0.85),
    "Colombia":      (1.55, 0.85),
    "Morocco":       (1.45, 0.75),
    "Japan":         (1.55, 0.90),
    "USA":           (1.45, 0.95),
    "Mexico":        (1.45, 0.95),
    "Switzerland":   (1.45, 0.90),
    "Senegal":       (1.40, 0.90),
    "Denmark":       (1.45, 0.90),
    "South Korea":   (1.35, 1.00),
    "Ecuador":       (1.30, 0.90),
    "Australia":     (1.20, 1.00),
    "Canada":        (1.30, 1.00),
    "Poland":        (1.30, 1.05),
    "Serbia":        (1.30, 1.05),
    "Ghana":         (1.25, 1.10),
    "Saudi Arabia":  (1.05, 1.15),
    "Costa Rica":    (0.95, 1.10),
    "New Zealand":   (0.95, 1.15),
    "Qatar":         (1.00, 1.20),
    "Panama":        (1.00, 1.10),
}

BASE_GOALS = 1.30          # league-average goals per team per game
HOME_ADVANTAGE = 1.25      # multiplier when not on neutral ground


def expected_goals(team, opp, is_home, neutral):
    atk, _ = TEAM_STRENGTH[team]
    _, opp_def = TEAM_STRENGTH[opp]
    mu = (atk / BASE_GOALS) * opp_def * BASE_GOALS
    if is_home and not neutral:
        mu *= HOME_ADVANTAGE
    return mu


def main(n_matches=2500, out="sample_matches.csv"):
    teams = list(TEAM_STRENGTH)
    rows = []
    dates = pd.date_range("2018-01-01", "2026-05-31", periods=n_matches)
    for date in dates:
        home, away = rng.choice(teams, size=2, replace=False)
        neutral = bool(rng.random() < 0.25)
        mu_h = expected_goals(home, away, True, neutral)
        mu_a = expected_goals(away, home, False, neutral)
        rows.append({
            "date": date.date().isoformat(),
            "home_team": home,
            "away_team": away,
            "home_score": rng.poisson(mu_h),
            "away_score": rng.poisson(mu_a),
            "tournament": "Friendly",
            "neutral": neutral,
        })
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} matches to {out}")


if __name__ == "__main__":
    main()
