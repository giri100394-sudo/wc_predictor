"""
Poisson match model.

Fits per-team attack and defense strengths from historical results via
maximum likelihood, then produces a full scoreline probability grid for
any fixture. The grid is what the EV optimizer consumes.

Data format (CSV) — matches the Kaggle international results dataset:
    date, home_team, away_team, home_score, away_score, tournament, neutral
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

MAX_GOALS = 10  # grid size; P(>10 goals) is negligible


@dataclass
class PoissonModel:
    decay_halflife_days: float = 730.0   # recent matches weigh more (2yr halflife)
    home_advantage: float = field(default=0.0, init=False)
    base_rate: float = field(default=0.0, init=False)
    attack: dict = field(default_factory=dict, init=False)
    defense: dict = field(default_factory=dict, init=False)

    # ------------------------------------------------------------------ fit
    def fit(self, df: pd.DataFrame, as_of: str | None = None) -> "PoissonModel":
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        if as_of:
            df = df[df["date"] <= pd.Timestamp(as_of)]
        ref_date = df["date"].max()
        age_days = (ref_date - df["date"]).dt.days.to_numpy(float)
        weights = 0.5 ** (age_days / self.decay_halflife_days)

        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)

        h = df["home_team"].map(idx).to_numpy()
        a = df["away_team"].map(idx).to_numpy()
        gh = df["home_score"].to_numpy(float)
        ga = df["away_score"].to_numpy(float)
        neutral = df["neutral"].astype(bool).to_numpy()

        # params: [attack(n), defense(n), home_adv, base]
        def nll(params):
            atk, dfn = params[:n], params[n:2 * n]
            home_adv, base = params[-2], params[-1]
            log_mu_h = base + atk[h] + dfn[a] + home_adv * (~neutral)
            log_mu_a = base + atk[a] + dfn[h]
            mu_h, mu_a = np.exp(log_mu_h), np.exp(log_mu_a)
            ll = weights * (gh * log_mu_h - mu_h + ga * log_mu_a - mu_a)
            # ridge penalty keeps strengths identifiable and shrinks
            # small-sample teams toward average
            return -ll.sum() + 0.1 * (np.sum(atk**2) + np.sum(dfn**2))

        x0 = np.zeros(2 * n + 2)
        x0[-1] = np.log(max(df[["home_score", "away_score"]].mean().mean(), 0.1))
        res = minimize(nll, x0, method="L-BFGS-B")
        if not res.success:
            raise RuntimeError(f"Model fit failed: {res.message}")

        atk, dfn = res.x[:n], res.x[n:2 * n]
        self.home_advantage, self.base_rate = res.x[-2], res.x[-1]
        self.attack = {t: atk[i] for t, i in idx.items()}
        self.defense = {t: dfn[i] for t, i in idx.items()}
        return self

    # -------------------------------------------------------------- predict
    def expected_goals(self, team_a: str, team_b: str,
                       neutral: bool = True) -> tuple[float, float]:
        """Expected goals for (team_a, team_b). World Cup => neutral=True,
        unless a host nation is playing at home."""
        for t in (team_a, team_b):
            if t not in self.attack:
                raise KeyError(f"Unknown team: {t!r}. Known: {sorted(self.attack)[:8]}...")
        log_mu_a = self.base_rate + self.attack[team_a] + self.defense[team_b]
        log_mu_b = self.base_rate + self.attack[team_b] + self.defense[team_a]
        if not neutral:
            log_mu_a += self.home_advantage  # team_a is the host
        return float(np.exp(log_mu_a)), float(np.exp(log_mu_b))

    def score_grid(self, team_a: str, team_b: str,
                   neutral: bool = True) -> np.ndarray:
        """(MAX_GOALS+1 x MAX_GOALS+1) matrix: grid[i, j] = P(a scores i, b scores j)."""
        mu_a, mu_b = self.expected_goals(team_a, team_b, neutral)
        pa = poisson.pmf(np.arange(MAX_GOALS + 1), mu_a)
        pb = poisson.pmf(np.arange(MAX_GOALS + 1), mu_b)
        grid = np.outer(pa, pb)
        return grid / grid.sum()  # renormalize tail mass
