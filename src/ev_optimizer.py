"""
Expected-value optimizer for the league's exact points system:

    Exact scoreline ............ 5 pts
    Correct result only ........ 3 pts  (never stacks with the 5)
    Wrong winner ............... -2 pts (only if you predicted a WIN and the
                                         OTHER team won; wrong draws cost 0,
                                         and a predicted win that ends in a
                                         draw costs 0)
    Picked player scores ....... +2 pts (independent of scoreline)

Strategy implications this module exploits:
  * Draw predictions are penalty-free => draws get an EV boost in close games.
  * A predicted win landing on a draw is 0, not -2 => the penalty only bites
    on the opposite-winner mass.
  * Scorer pick decouples => just maximize P(player scores >= 1) over BOTH teams.
"""

from dataclasses import dataclass

import numpy as np

PTS_EXACT = 5
PTS_RESULT = 3
PTS_WRONG_WINNER = -2
PTS_SCORER = 2


@dataclass(frozen=True)
class ScorelineEV:
    score_a: int
    score_b: int
    ev: float
    p_exact: float
    p_result: float       # P(predicted result class occurs)
    p_opposite_win: float  # mass that triggers the -2 (0 for draw predictions)


def _result_masses(grid: np.ndarray) -> tuple[float, float, float]:
    """Return (P(a wins), P(draw), P(b wins)) from a scoreline grid."""
    p_a = float(np.tril(grid, -1).sum())   # rows = a's goals, i > j
    p_draw = float(np.trace(grid))
    p_b = float(np.triu(grid, 1).sum())
    return p_a, p_draw, p_b


def scoreline_evs(grid: np.ndarray, max_shown_goals: int = 5) -> list[ScorelineEV]:
    """EV of every candidate scoreline prediction, best first."""
    p_a_win, p_draw, p_b_win = _result_masses(grid)
    out = []
    for i in range(max_shown_goals + 1):
        for j in range(max_shown_goals + 1):
            p_exact = float(grid[i, j])
            if i > j:
                p_result, p_opp = p_a_win, p_b_win
            elif i < j:
                p_result, p_opp = p_b_win, p_a_win
            else:
                p_result, p_opp = p_draw, 0.0  # draws: no penalty, ever
            ev = (PTS_EXACT * p_exact
                  + PTS_RESULT * (p_result - p_exact)
                  + PTS_WRONG_WINNER * p_opp)
            out.append(ScorelineEV(i, j, ev, p_exact, p_result, p_opp))
    out.sort(key=lambda s: s.ev, reverse=True)
    return out


@dataclass(frozen=True)
class ScorerEV:
    player: str
    team: str
    p_scores: float

    @property
    def ev(self) -> float:
        return PTS_SCORER * self.p_scores


def scorer_evs(mu_a: float, mu_b: float,
               players_a: list[dict], players_b: list[dict]) -> list[ScorerEV]:
    """
    Rank players from BOTH teams by P(scores >= 1).

    Each player dict needs:
        name:        str
        goal_share:  fraction of the team's goals they typically score (0..1)
        p_start:     probability they play meaningful minutes (0..1)
        minutes_frac: expected fraction of the match played if they do (0..1)

    Player goals ~ Poisson(team_xg * goal_share * minutes_frac), conditioned
    on playing. P(scores) = p_start * (1 - exp(-rate)).
    """
    out = []
    for team_mu, players, team_label in ((mu_a, players_a, "A"), (mu_b, players_b, "B")):
        for p in players:
            rate = team_mu * p["goal_share"] * p.get("minutes_frac", 1.0)
            p_scores = p.get("p_start", 1.0) * (1.0 - np.exp(-rate))
            out.append(ScorerEV(p["name"], p.get("team", team_label), float(p_scores)))
    out.sort(key=lambda s: s.p_scores, reverse=True)
    return out


def best_prediction(grid: np.ndarray, mu_a: float, mu_b: float,
                    players_a: list[dict], players_b: list[dict]) -> dict:
    """The single highest-EV (scoreline, scorer) prediction plus alternatives."""
    scores = scoreline_evs(grid)
    scorers = scorer_evs(mu_a, mu_b, players_a, players_b)
    total = scores[0].ev + (scorers[0].ev if scorers else 0.0)
    return {
        "scoreline": scores[0],
        "scorer": scorers[0] if scorers else None,
        "expected_points": total,
        "scoreline_alternatives": scores[1:6],
        "scorer_alternatives": scorers[1:6],
    }
