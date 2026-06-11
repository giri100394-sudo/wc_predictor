"""
LRMC-style Markov chain ranking model, adapted for soccer.

Loosely follows Kvam & Sokol, "A Logistic Regression/Markov Chain Model
For NCAA Basketball" (Naval Research Logistics 53, 2006):
https://www2.isye.gatech.edu/~jsokol/ncaa.pdf

Core idea: a "random voter" walks between teams. After watching game
(i, j), the voter currently believing team i is best moves to j with
probability r_x = P(j is better than i | margin x), and stays with
probability 1 - r_x. r_x is estimated via logistic regression on margin
of victory, so blowouts shift belief more than narrow wins. The
steady-state distribution of the walk ranks the teams.

Soccer adaptation notes (the paper is built around NCAA's home-and-home
conference schedule, which doesn't exist for international football):
  - r_x is fit on "matched pairs": teams that played each other both home
    and away. x = the neutral-court-adjusted goal margin in the first
    leg; the label is whether the same team also avoided losing the
    return leg. A single-parameter, no-intercept logistic
    r_x = sigmoid(b * x) is used so that r_(-x) = 1 - r_x by
    construction (P(i better) and P(j better) must sum to 1 for the
    same game).
  - Home advantage is estimated directly from the data (difference in
    average goal margin between home and neutral fixtures) and used to
    convert raw margins to neutral-court margins before everything else.
  - The transition matrix is mixed with a small teleport toward each
    team's own activity share (rather than uniform 1/n) to keep the
    chain ergodic without letting rarely-played minor teams dominate the
    steady state -- a 336-team international dataset is far more sparse
    and disconnected than an NCAA conference.
  - The paper's eq. (6) (steady-state difference -> point spread) is
    refit here as: neutral_margin ~ rating_scale * (pi_home - pi_away),
    via weighted least squares through the origin.
  - To plug into the same EV optimizer as the Poisson model, the rating
    difference is converted into expected goals by splitting the
    league-average total goals around the predicted goal difference.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.linalg import eig
from scipy.optimize import minimize_scalar
from scipy.stats import poisson

MAX_GOALS = 10


def _matched_pair_examples(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Build (x, y) training pairs from teams that played home-and-away.

    x = neutral-court goal margin of the first leg (from the home team's
    perspective). y = 1 if that same team also avoided losing the return
    leg (on a neutral-court basis), 0 if they lost it, 0.5 if it was an
    exact draw on a neutral-court basis.
    """
    groups: dict[tuple[str, str], list] = {}
    for row in df.itertuples(index=False):
        key = (row.home_team, row.away_team) if row.home_team < row.away_team \
            else (row.away_team, row.home_team)
        groups.setdefault(key, []).append(row)

    xs, ys = [], []
    for games in groups.values():
        if len(games) < 2:
            continue
        games = sorted(games, key=lambda g: g.date)
        for g in games:
            for g2 in games:
                if g2 is g or g2.home_team == g.home_team:
                    continue
                x = g.neutral_margin
                y2 = -g2.neutral_margin  # g.home_team's perspective in g2 (away there)
                y = 1.0 if y2 > 0 else (0.0 if y2 < 0 else 0.5)
                xs.append(x)
                ys.append(y)
                break
    return np.array(xs), np.array(ys)


def _fit_sensitivity(xs: np.ndarray, ys: np.ndarray) -> float:
    """Fit b in r_x = sigmoid(b * x) via weighted MLE (no intercept)."""
    def bce(b):
        p = 1.0 / (1.0 + np.exp(-b * xs))
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return -np.mean(ys * np.log(p) + (1 - ys) * np.log(1 - p))

    res = minimize_scalar(bce, bounds=(1e-3, 5.0), method="bounded")
    return float(res.x)


@dataclass
class MarkovModel:
    decay_halflife_days: float = 730.0
    teleport_eps: float = 0.05  # mixes in a small restart toward active teams
    home_advantage: float = field(default=0.0, init=False)
    sensitivity: float = field(default=0.0, init=False)   # b in r_x = sigmoid(b*x)
    rating_scale: float = field(default=0.0, init=False)  # C in margin ~ C*(pi_i - pi_j)
    avg_total_goals: float = field(default=0.0, init=False)
    pi: dict = field(default_factory=dict, init=False)

    # ------------------------------------------------------------------ fit
    def fit(self, df: pd.DataFrame, as_of: str | None = None) -> "MarkovModel":
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        if as_of:
            df = df[df["date"] <= pd.Timestamp(as_of)]
        df = df.dropna(subset=["home_score", "away_score"])

        ref_date = df["date"].max()
        age_days = (ref_date - df["date"]).dt.days.to_numpy(float)
        weights = 0.5 ** (age_days / self.decay_halflife_days)

        margin = (df["home_score"] - df["away_score"]).to_numpy(float)
        is_home = (~df["neutral"].astype(bool)).to_numpy(float)

        # home advantage: weighted avg margin, non-neutral minus neutral games
        nn = is_home.astype(bool)
        if nn.any() and (~nn).any():
            self.home_advantage = max(
                np.average(margin[nn], weights=weights[nn])
                - np.average(margin[~nn], weights=weights[~nn]), 0.0)
        else:
            self.home_advantage = 0.0

        df["neutral_margin"] = margin - self.home_advantage * is_home

        # 1. matched home-and-away pairs -> sensitivity of belief to margin
        xs, ys = _matched_pair_examples(df)
        self.sensitivity = _fit_sensitivity(xs, ys) if len(xs) >= 20 else 0.2

        # 2. transition matrix: random voter moves toward the team that
        #    "looked better" in each game, weighted by recency
        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)
        h_idx = df["home_team"].map(idx).to_numpy()
        a_idx = df["away_team"].map(idx).to_numpy()
        r = 1.0 / (1.0 + np.exp(-self.sensitivity * df["neutral_margin"].to_numpy()))

        T = np.zeros((n, n))
        Wt = np.zeros(n)
        np.add.at(T, (h_idx, h_idx), weights * r)
        np.add.at(T, (h_idx, a_idx), weights * (1 - r))
        np.add.at(T, (a_idx, h_idx), weights * r)
        np.add.at(T, (a_idx, a_idx), weights * (1 - r))
        np.add.at(Wt, h_idx, weights)
        np.add.at(Wt, a_idx, weights)
        T /= Wt[:, None]

        # teleport toward each team's own activity share, keeps the chain
        # ergodic without letting rarely-played teams dominate the steady
        # state purely because they have few exits
        v = Wt / Wt.sum()
        T = (1 - self.teleport_eps) * T + self.teleport_eps * np.outer(np.ones(n), v)

        # 3. steady-state distribution: left eigenvector for eigenvalue 1
        vals, vecs = eig(T.T)
        i1 = int(np.argmin(np.abs(vals - 1)))
        pi = np.real(vecs[:, i1])
        pi /= pi.sum()
        self.pi = {t: pi[i] for t, i in idx.items()}

        # 4. calibrate steady-state gap -> goal margin (analogue of eq. 6)
        pi_diff = pi[h_idx] - pi[a_idx]
        denom = np.sum(weights * pi_diff ** 2)
        self.rating_scale = float(
            np.sum(weights * df["neutral_margin"].to_numpy() * pi_diff) / denom
        ) if denom > 0 else 0.0

        # 5. league-average total goals, used to split the margin into mu_a/mu_b
        self.avg_total_goals = float(
            np.average(df["home_score"] + df["away_score"], weights=weights))
        return self

    # -------------------------------------------------------------- predict
    def expected_goals(self, team_a: str, team_b: str,
                       neutral: bool = True) -> tuple[float, float]:
        """Expected goals for (team_a, team_b). World Cup => neutral=True,
        unless a host nation is playing at home."""
        for t in (team_a, team_b):
            if t not in self.pi:
                raise KeyError(f"Unknown team: {t!r}. Known: {sorted(self.pi)[:8]}...")
        diff = self.rating_scale * (self.pi[team_a] - self.pi[team_b])
        if not neutral:
            diff += self.home_advantage  # team_a is the host
        total = self.avg_total_goals
        mu_a = max((total + diff) / 2, 0.05)
        mu_b = max((total - diff) / 2, 0.05)
        return mu_a, mu_b

    def score_grid(self, team_a: str, team_b: str,
                   neutral: bool = True) -> np.ndarray:
        """(MAX_GOALS+1 x MAX_GOALS+1) matrix: grid[i, j] = P(a scores i, b scores j)."""
        mu_a, mu_b = self.expected_goals(team_a, team_b, neutral)
        pa = poisson.pmf(np.arange(MAX_GOALS + 1), mu_a)
        pb = poisson.pmf(np.arange(MAX_GOALS + 1), mu_b)
        grid = np.outer(pa, pb)
        return grid / grid.sum()
