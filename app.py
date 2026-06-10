"""
World Cup Prediction-League Agent — web UI.

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from poisson_model import PoissonModel
from ev_optimizer import best_prediction, scoreline_evs, scorer_evs
import tracker

MATCHES_CSV = ROOT / "data" / "sample_matches.csv"
PLAYERS_CSV = ROOT / "data" / "sample_players.csv"

st.set_page_config(page_title="WC Prediction Agent", page_icon="⚽", layout="wide")


# ----------------------------------------------------------------- caching
@st.cache_resource(show_spinner="Fitting model on match history…")
def get_model(matches_path: str) -> PoissonModel:
    return PoissonModel().fit(pd.read_csv(matches_path))


@st.cache_data
def get_players(players_path: str) -> pd.DataFrame:
    return pd.read_csv(players_path)


model = get_model(str(MATCHES_CSV))
players_df = get_players(str(PLAYERS_CSV))
teams = sorted(model.attack)

st.title("⚽ World Cup Prediction-League Agent")
st.caption("Optimized for your league: 5 exact · 3 result · −2 wrong winner "
           "(draws penalty-free) · +2 scorer")

tab_predict, tab_result, tab_report = st.tabs(
    ["🎯 Predict", "📋 Log result", "📈 Feedback report"])

# ================================================================= PREDICT
with tab_predict:
    c1, c2, c3 = st.columns([2, 2, 1])
    team_a = c1.selectbox("Team A", teams, index=teams.index("France") if "France" in teams else 0)
    team_b = c2.selectbox("Team B", teams, index=teams.index("England") if "England" in teams else 1)
    host = c3.selectbox("Host advantage", ["Neutral", team_a, team_b])

    if team_a == team_b:
        st.warning("Pick two different teams.")
        st.stop()

    a, b = (team_b, team_a) if host == team_b else (team_a, team_b)
    neutral = host == "Neutral"

    mu_a, mu_b = model.expected_goals(a, b, neutral=neutral)
    grid = model.score_grid(a, b, neutral=neutral)
    pa = players_df[players_df["team"] == a].to_dict("records")
    pb = players_df[players_df["team"] == b].to_dict("records")
    rec = best_prediction(grid, mu_a, mu_b, pa, pb)
    s, sc = rec["scoreline"], rec["scorer"]

    p_a = float(np.tril(grid, -1).sum())
    p_d = float(np.trace(grid))
    p_b = float(np.triu(grid, 1).sum())

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{a} win", f"{p_a:.0%}")
    m2.metric("Draw", f"{p_d:.0%}")
    m3.metric(f"{b} win", f"{p_b:.0%}")
    m4.metric("Expected goals", f"{mu_a:.2f} – {mu_b:.2f}")

    st.subheader(f"Recommended: **{a} {s.score_a} – {s.score_b} {b}**")
    why = ("a draw pick carries zero penalty risk in your league"
           if s.score_a == s.score_b else
           "the result probability outweighs the wrong-winner risk")
    st.write(f"Expected value **{s.ev:+.2f} pts** — exact-hit chance "
             f"{s.p_exact:.1%}, correct-result chance {s.p_result:.1%}; {why}.")
    if sc:
        st.write(f"**Scorer pick: {sc.player}** ({sc.team}) — "
                 f"{sc.p_scores:.0%} chance of scoring, worth {sc.ev:+.2f} pts of EV.")
    st.write(f"**Total expected points: {rec['expected_points']:.2f} / 7**")

    left, right = st.columns(2)
    with left:
        st.markdown("**Scoreline alternatives (by EV)**")
        alt = pd.DataFrame([{
            "Score": f"{x.score_a}–{x.score_b}",
            "EV (pts)": round(x.ev, 2),
            "P(exact)": f"{x.p_exact:.1%}",
            "Penalty risk": f"{x.p_opposite_win:.0%}",
        } for x in [s] + rec["scoreline_alternatives"]])
        st.dataframe(alt, hide_index=True, width='stretch')
    with right:
        st.markdown("**Scorer alternatives**")
        if sc:
            alts = pd.DataFrame([{
                "Player": x.player, "Team": x.team,
                "P(scores)": f"{x.p_scores:.0%}",
                "EV (pts)": round(x.ev, 2),
            } for x in [sc] + rec["scorer_alternatives"]])
            st.dataframe(alts, hide_index=True, width='stretch')
        else:
            st.info("No player data for these teams yet — add rows to "
                    "data/sample_players.csv.")

    st.divider()
    st.markdown("**Save this prediction** (before kickoff — it locks in the league, "
                "and logging it here powers the feedback report)")
    f1, f2, f3, f4 = st.columns([1, 1, 2, 1])
    pred_a = f1.number_input(f"{a} goals", 0, 10, int(s.score_a))
    pred_b = f2.number_input(f"{b} goals", 0, 10, int(s.score_b))
    scorer_options = [x.player for x in ([sc] + rec["scorer_alternatives"])] if sc else ["(none)"]
    pick = f3.selectbox("Scorer pick", scorer_options)
    if f4.button("Save prediction", type="primary", width='stretch'):
        mid = tracker.log_prediction(a, b, int(pred_a), int(pred_b), pick,
                                     rec["expected_points"])
        st.success(f"Saved as `{mid}` — enter the real result in the next tab "
                   "after the final whistle.")

# ============================================================== LOG RESULT
with tab_result:
    preds = tracker._load(tracker.PRED_LOG, tracker.PRED_COLS)
    results = tracker._load(tracker.RESULT_LOG, tracker.RESULT_COLS)
    pending = preds[~preds["match_id"].isin(results["match_id"])]
    if pending.empty:
        st.info("No pending matches. Save a prediction first.")
    else:
        row = pending.iloc[
            [pending["match_id"].tolist().index(
                st.selectbox("Match", pending["match_id"]))]].iloc[0]
        st.write(f"Your prediction: **{row.team_a} {row.pred_a} – "
                 f"{row.pred_b} {row.team_b}**, scorer **{row.scorer}**")
        r1, r2, r3 = st.columns(3)
        actual_a = r1.number_input(f"{row.team_a} actual goals", 0, 15, 0)
        actual_b = r2.number_input(f"{row.team_b} actual goals", 0, 15, 0)
        scored = r3.checkbox(f"{row.scorer} scored?")
        if st.button("Save result", type="primary"):
            tracker.log_result(row.match_id, int(actual_a), int(actual_b), scored)
            pts = tracker.score_prediction(row.pred_a, row.pred_b,
                                           int(actual_a), int(actual_b), scored)
            st.success(f"Scored: **{pts['total']:+d} pts** "
                       f"({pts['outcome']} {pts['scoreline_points']:+d}, "
                       f"scorer {pts['scorer_points']:+d})")

# ================================================================== REPORT
with tab_report:
    rep = tracker.feedback_report()
    if rep["matches_scored"] == 0:
        st.info(rep["message"])
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Matches scored", rep["matches_scored"])
        k2.metric("Total points", rep["total_points"])
        k3.metric("Avg pts / match", rep["avg_points_per_match"])
        k4.metric("Scorer hit rate", f"{rep['scorer_hit_rate']:.0%}")
        st.write(f"Exact hits: **{rep['exact_hits']}** · "
                 f"Correct results: **{rep['result_hits']}** · "
                 f"Wrong winners: **{rep['wrong_winners']}**")
        st.markdown("**Refinement hints**")
        for h in rep["refinement_hints"]:
            st.write(f"- {h}")
        st.markdown("**Match by match**")
        st.dataframe(rep["per_match"], hide_index=True, width='stretch')
