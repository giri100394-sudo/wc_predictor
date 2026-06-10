"""
Prediction tracker & feedback loop.

Logs every prediction you make, scores it against the actual result using the
league's exact rules, and builds a feedback report showing where the model is
strong or weak — so refinements are driven by evidence, not vibes.

Files (created automatically in data/):
    predictions_log.csv   one row per prediction
    results_log.csv       one row per completed match
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRED_LOG = ROOT / "data" / "predictions_log.csv"
RESULT_LOG = ROOT / "data" / "results_log.csv"

PRED_COLS = ["match_id", "team_a", "team_b", "pred_a", "pred_b",
             "scorer", "model_ev", "logged_at"]
RESULT_COLS = ["match_id", "actual_a", "actual_b", "scorer_scored", "entered_at"]


def _load(path: Path, cols: list[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=cols)


def log_prediction(team_a: str, team_b: str, pred_a: int, pred_b: int,
                   scorer: str, model_ev: float, match_id: str | None = None) -> str:
    """Save (or overwrite) your prediction for a match. Returns the match_id."""
    match_id = match_id or f"{team_a}_vs_{team_b}".replace(" ", "")
    df = _load(PRED_LOG, PRED_COLS)
    df = df[df["match_id"] != match_id]  # latest save replaces previous, like the league
    row = {"match_id": match_id, "team_a": team_a, "team_b": team_b,
           "pred_a": pred_a, "pred_b": pred_b, "scorer": scorer,
           "model_ev": round(model_ev, 3),
           "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    PRED_LOG.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PRED_LOG, index=False)
    return match_id


def log_result(match_id: str, actual_a: int, actual_b: int,
               scorer_scored: bool) -> None:
    """Enter the real result after the match ends."""
    df = _load(RESULT_LOG, RESULT_COLS)
    df = df[df["match_id"] != match_id]
    row = {"match_id": match_id, "actual_a": actual_a, "actual_b": actual_b,
           "scorer_scored": bool(scorer_scored),
           "entered_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_LOG, index=False)


def _result_class(a: int, b: int) -> str:
    return "A" if a > b else ("B" if b > a else "D")


def score_prediction(pred_a: int, pred_b: int, actual_a: int, actual_b: int,
                     scorer_scored: bool) -> dict:
    """Apply the league rules to one match."""
    pts, outcome = 0, "wrong"
    pc, ac = _result_class(pred_a, pred_b), _result_class(actual_a, actual_b)
    if (pred_a, pred_b) == (actual_a, actual_b):
        pts, outcome = 5, "exact"
    elif pc == ac:
        pts, outcome = 3, "result"
    elif pc != "D" and ac != "D":          # predicted a winner, the OTHER side won
        pts, outcome = -2, "wrong_winner"
    # predicted draw & wrong, or predicted win & actual draw => 0, no penalty
    scorer_pts = 2 if scorer_scored else 0
    return {"scoreline_points": pts, "scorer_points": scorer_pts,
            "total": pts + scorer_pts, "outcome": outcome}


def feedback_report() -> dict:
    """Join predictions to results and summarize how the model is doing."""
    preds = _load(PRED_LOG, PRED_COLS)
    results = _load(RESULT_LOG, RESULT_COLS)
    if preds.empty:
        return {"matches_scored": 0, "message": "No predictions logged yet."}
    df = preds.merge(results, on="match_id", how="inner")
    if df.empty:
        return {"matches_scored": 0, "pending": len(preds),
                "message": f"{len(preds)} prediction(s) logged, none completed yet."}

    scored = df.apply(lambda r: score_prediction(
        r.pred_a, r.pred_b, r.actual_a, r.actual_b, r.scorer_scored), axis=1)
    df = pd.concat([df, pd.DataFrame(list(scored))], axis=1)

    n = len(df)
    rep = {
        "matches_scored": n,
        "total_points": int(df["total"].sum()),
        "avg_points_per_match": round(df["total"].mean(), 2),
        "exact_hits": int((df["outcome"] == "exact").sum()),
        "result_hits": int((df["outcome"] == "result").sum()),
        "wrong_winners": int((df["outcome"] == "wrong_winner").sum()),
        "scorer_hit_rate": round(df["scorer_scored"].mean(), 2),
        "per_match": df[["match_id", "pred_a", "pred_b", "actual_a", "actual_b",
                         "outcome", "scorer", "scorer_scored", "total"]],
    }

    # ---- refinement hints -------------------------------------------------
    hints = []
    if n >= 5:
        goals_err = ((df.pred_a + df.pred_b) - (df.actual_a + df.actual_b)).mean()
        if goals_err > 0.7:
            hints.append("Model predicts too many goals on average — consider "
                         "lowering attack ratings or adding Dixon-Coles.")
        elif goals_err < -0.7:
            hints.append("Model predicts too few goals — attack ratings may be "
                         "shrunk too hard (lower the ridge penalty).")
        ww = rep["wrong_winners"] / n
        if ww > 0.30:
            hints.append("High wrong-winner rate — lean on draw predictions more "
                         "in close matches; they're penalty-free in your league.")
        if rep["scorer_hit_rate"] < 0.30:
            hints.append("Scorer hit rate is low — update p_start from confirmed "
                         "lineups before each lock, it's the biggest lever.")
    else:
        hints.append("Fewer than 5 completed matches — keep logging before "
                     "drawing conclusions; small samples lie.")
    rep["refinement_hints"] = hints
    return rep
