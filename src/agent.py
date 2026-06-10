"""
Agent layer: an LLM orchestrates the statistical model as a tool, then layers
on context the model can't see (injuries, rotation risk after a team has
already qualified, weather, etc.) before producing a final recommendation.

Requires:  pip install anthropic   and  ANTHROPIC_API_KEY in your environment.

Usage:
    python src/agent.py "France" "England" --context "Mbappé doubtful (ankle)"
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from poisson_model import PoissonModel
from ev_optimizer import best_prediction, scoreline_evs, scorer_evs

ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------- tools

def tool_predict_match(team_a: str, team_b: str, host: str | None = None,
                       matches_csv: str | None = None,
                       players_csv: str | None = None) -> dict:
    """Run the EV optimizer; returns a JSON-serializable summary the LLM reads."""
    matches_csv = matches_csv or str(ROOT / "data" / "sample_matches.csv")
    players_csv = players_csv or str(ROOT / "data" / "sample_players.csv")

    model = PoissonModel().fit(pd.read_csv(matches_csv))
    neutral = host is None
    a, b = (team_b, team_a) if host == team_b else (team_a, team_b)

    mu_a, mu_b = model.expected_goals(a, b, neutral=neutral)
    grid = model.score_grid(a, b, neutral=neutral)
    pdf = pd.read_csv(players_csv)
    pa = pdf[pdf["team"] == a].to_dict("records")
    pb = pdf[pdf["team"] == b].to_dict("records")
    rec = best_prediction(grid, mu_a, mu_b, pa, pb)

    return {
        "fixture": f"{a} vs {b}",
        "expected_goals": {a: round(mu_a, 2), b: round(mu_b, 2)},
        "recommended_scoreline": f"{rec['scoreline'].score_a}-{rec['scoreline'].score_b}",
        "scoreline_ev": round(rec["scoreline"].ev, 3),
        "recommended_scorer": rec["scorer"].player if rec["scorer"] else None,
        "scorer_probability": round(rec["scorer"].p_scores, 3) if rec["scorer"] else None,
        "total_expected_points": round(rec["expected_points"], 2),
        "alternatives": [
            {"score": f"{alt.score_a}-{alt.score_b}", "ev": round(alt.ev, 3)}
            for alt in rec["scoreline_alternatives"]
        ],
        "scorer_alternatives": [
            {"player": alt.player, "team": alt.team, "p": round(alt.p_scores, 3)}
            for alt in rec["scorer_alternatives"]
        ],
    }


TOOLS = [{
    "name": "predict_match",
    "description": ("Statistical EV-optimized prediction for a fixture under the "
                    "league rules (5 exact / 3 result / -2 wrong winner, draws "
                    "penalty-free / +2 scorer). Returns recommendation + alternatives."),
    "input_schema": {
        "type": "object",
        "properties": {
            "team_a": {"type": "string"},
            "team_b": {"type": "string"},
            "host": {"type": "string", "description": "optional host-nation team name"},
        },
        "required": ["team_a", "team_b"],
    },
}]

SYSTEM = """You are a World Cup prediction-league strategist. The league rules:
5 pts exact scoreline; 3 pts correct result; -2 only when a predicted winner
loses (draw predictions are never penalized); +2 if the picked player scores.

Call predict_match for the baseline, then adjust for the user-supplied context
(injuries, rotation, motivation, weather). Prefer draws in coin-flip matches
because they carry no penalty risk. The scorer pick is independent — choose the
highest P(scores) from either team unless context rules them out. Finish with:
final scoreline, final scorer pick, expected points, and a 2-3 sentence rationale."""


def run_agent(team_a: str, team_b: str, context: str = "", host: str | None = None):
    import anthropic  # deferred so the statistical stack works without it
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content":
                 f"Fixture: {team_a} vs {team_b}."
                 + (f" Host: {host}." if host else " Neutral venue.")
                 + (f" Context: {context}" if context else "")}]

    while True:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1500,
            system=SYSTEM, tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = tool_predict_match(**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("team_a")
    ap.add_argument("team_b")
    ap.add_argument("--context", default="")
    ap.add_argument("--host", default=None)
    args = ap.parse_args()
    print(run_agent(args.team_a, args.team_b, args.context, args.host))
