"""
FastAPI backend for the World Cup 2026 Prediction Agent React app.

Serves Poisson and Markov-chain predictions for every FIFA World Cup
group-stage fixture from 2026-06-11 onward, plus actual results as they're
filled into data/sample_matches.csv (models + cache refit automatically
whenever that file changes).

Usage:
    uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from poisson_model import PoissonModel  # noqa: E402
from markov_model import MarkovModel  # noqa: E402
from ev_optimizer import scoreline_evs, scorer_evs  # noqa: E402
from tracker import score_prediction  # noqa: E402
from scorer_agent import web_top_scorers  # noqa: E402

MATCHES_CSV = ROOT / "data" / "sample_matches.csv"
PLAYERS_CSV = ROOT / "data" / "sample_players.csv"

WC_START = "2026-06-11"
WC_TOURNAMENT = "FIFA World Cup"

# the players sample CSV may use a different name for the same team
PLAYER_TEAM_ALIASES = {"United States": "USA", "USA": "United States"}

app = FastAPI(title="World Cup 2026 Prediction API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict = {"mtime": None, "fixtures": None}


def team_players(players_df: pd.DataFrame, team: str) -> list[dict]:
    names = {team, PLAYER_TEAM_ALIASES.get(team, team)}
    return players_df[players_df["team"].isin(names)].to_dict("records")


def result_probs(grid: np.ndarray) -> tuple[float, float, float]:
    p_a = float(np.tril(grid, -1).sum())
    p_d = float(np.trace(grid))
    p_b = float(np.triu(grid, 1).sum())
    return p_a, p_d, p_b


def team_recent_form(df: pd.DataFrame, team: str, before: pd.Timestamp, n: int = 5) -> list[dict]:
    """Last n played results for `team` before `before`, most recent first."""
    mask = ((df["home_team"] == team) | (df["away_team"] == team)) \
        & (df["date"] < before) & df["home_score"].notna()
    sub = df[mask].sort_values("date", ascending=False).head(n)

    out = []
    for _, m in sub.iterrows():
        is_home = m.home_team == team
        gf = int(m.home_score if is_home else m.away_score)
        ga = int(m.away_score if is_home else m.home_score)
        result = "W" if gf > ga else ("L" if gf < ga else "D")
        out.append({
            "date": m.date.strftime("%Y-%m-%d"),
            "opponent": m.away_team if is_home else m.home_team,
            "score_for": gf,
            "score_against": ga,
            "result": result,
            "tournament": m.tournament,
        })
    return out


def build_fixtures() -> list[dict]:
    df = pd.read_csv(MATCHES_CSV, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    players_df = pd.read_csv(PLAYERS_CSV, encoding="utf-8")

    poisson = PoissonModel().fit(df)
    markov = MarkovModel().fit(df)
    known = set(poisson.attack) & set(markov.pi)

    wc = df[(df["date"] >= WC_START) & (df["tournament"] == WC_TOURNAMENT)]
    wc = wc[wc["home_team"].isin(known) & wc["away_team"].isin(known)]
    wc = wc.sort_values("date").reset_index(drop=True)

    fixtures = []
    for i, m in wc.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        has_actual = pd.notna(m.home_score)
        actual = ({"home": int(m.home_score), "away": int(m.away_score)}
                  if has_actual else None)

        models = {}
        for name, model in [("poisson", poisson), ("markov", markov)]:
            grid = model.score_grid(a, b, neutral=neutral)
            pick = scoreline_evs(grid)[0]
            p_a, p_d, p_b = result_probs(grid)
            entry = {
                "score": [pick.score_a, pick.score_b],
                "probs": {"home": p_a, "draw": p_d, "away": p_b},
                "p_exact": pick.p_exact,
                "ev": pick.ev,
            }
            if has_actual:
                sc = score_prediction(pick.score_a, pick.score_b,
                                       actual["home"], actual["away"], False)
                entry["outcome"] = sc["outcome"]
                entry["points"] = sc["scoreline_points"]
            models[name] = entry

        mu_a, mu_b = poisson.expected_goals(a, b, neutral=neutral)
        pa = team_players(players_df, a)
        pb = team_players(players_df, b)

        web_scorers = web_top_scorers(a, b)
        if web_scorers:
            top_scorers_out = web_scorers[:3]
            scorer_source = "web"
        else:
            top_scorers = scorer_evs(mu_a, mu_b, pa, pb)[:3]
            top_scorers_out = [
                {"player": s.player, "team": s.team,
                 "probability_pct": round(s.p_scores * 100, 1)}
                for s in top_scorers
            ]
            scorer_source = "model"

        fixtures.append({
            "id": int(i),
            "date": m.date.strftime("%Y-%m-%d"),
            "home_team": a,
            "away_team": b,
            "neutral": neutral,
            "venue": "Neutral" if neutral else f"{a} (host)",
            "actual": actual,
            "models": models,
            "recent_form": {
                "home": team_recent_form(df, a, m.date),
                "away": team_recent_form(df, b, m.date),
            },
            "top_scorers": top_scorers_out,
            "scorer_source": scorer_source,
        })
    return fixtures


def get_fixtures() -> list[dict]:
    mtime = MATCHES_CSV.stat().st_mtime
    if _cache["mtime"] != mtime:
        _cache["fixtures"] = build_fixtures()
        _cache["mtime"] = mtime
    return _cache["fixtures"]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/fixtures")
def fixtures():
    return get_fixtures()


@app.post("/api/refresh-scorers/{date}")
def refresh_scorers(date: str):
    """Force a live web lookup of scorer predictions for every WC2026 fixture
    on `date` (YYYY-MM-DD), overwriting the cache. Costs real API calls."""
    df = pd.read_csv(MATCHES_CSV, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    day = df[(df["date"] == pd.Timestamp(date)) & (df["tournament"] == WC_TOURNAMENT)]

    results = []
    for _, m in day.iterrows():
        a, b = m.home_team, m.away_team
        data = web_top_scorers(a, b, use_cache=False, fetch_live=True)
        results.append({"home_team": a, "away_team": b, "ok": data is not None})

    _cache["mtime"] = None  # force fixtures rebuild on next /api/fixtures
    return {
        "date": date,
        "total": len(results),
        "updated": sum(1 for r in results if r["ok"]),
        "results": results,
    }
