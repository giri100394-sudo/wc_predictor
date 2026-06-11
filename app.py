"""
World Cup Prediction Agent — single-page web UI.

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
from ev_optimizer import best_prediction

MATCHES_CSV = ROOT / "data" / "sample_matches.csv"
PLAYERS_CSV = ROOT / "data" / "sample_players.csv"

EMBLEM_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/"
               "2026_FIFA_World_Cup_emblem.svg/250px-2026_FIFA_World_Cup_emblem.svg.png")
TROPHY_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/"
              "Golden_trophy.svg/250px-Golden_trophy.svg.png")

FLAGS = {
    "Argentina": "🇦🇷", "Australia": "🇦🇺", "Belgium": "🇧🇪", "Brazil": "🇧🇷",
    "Canada": "🇨🇦", "Colombia": "🇨🇴", "Costa Rica": "🇨🇷", "Croatia": "🇭🇷",
    "Denmark": "🇩🇰", "Ecuador": "🇪🇨", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷",
    "Germany": "🇩🇪", "Ghana": "🇬🇭", "Italy": "🇮🇹", "Japan": "🇯🇵",
    "Mexico": "🇲🇽", "Morocco": "🇲🇦", "Netherlands": "🇳🇱", "New Zealand": "🇳🇿",
    "Panama": "🇵🇦", "Poland": "🇵🇱", "Portugal": "🇵🇹", "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦", "Senegal": "🇸🇳", "Serbia": "🇷🇸", "South Korea": "🇰🇷",
    "Spain": "🇪🇸", "Switzerland": "🇨🇭", "USA": "🇺🇸", "Uruguay": "🇺🇾",
}


def flag(team: str) -> str:
    return FLAGS.get(team, "🏳️")


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

# ----------------------------------------------------------------- styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

.hero-banner {
    background: linear-gradient(120deg, #0E4D32 0%, #16291F 55%, #1B3358 100%);
    border: 1px solid rgba(232, 179, 57, 0.35);
    border-radius: 22px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 1.6rem;
    flex-wrap: wrap;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}
.hero-banner img { height: 96px; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.4)); }
.hero-title { font-size: 2.1rem; font-weight: 800; color: #F2EFE6; margin: 0; }
.hero-sub { color: #E8B339; font-weight: 600; margin: 0.15rem 0 0.4rem 0; }
.hero-caption { color: #C7CCC4; font-size: 0.92rem; margin: 0; }

.prob-bar-wrap {
    display: flex; height: 14px; border-radius: 8px; overflow: hidden;
    margin: 0.6rem 0 1rem 0; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

.rec-card {
    background: linear-gradient(120deg, rgba(232,179,57,0.16), rgba(14,77,50,0.35));
    border: 1px solid rgba(232,179,57,0.45);
    border-radius: 18px;
    padding: 1.4rem 1.8rem;
    text-align: center;
    margin-bottom: 0.6rem;
}
.rec-card img { height: 46px; vertical-align: middle; margin-right: 0.6rem; }
.rec-score { font-size: 2.4rem; font-weight: 800; color: #E8B339; }
.rec-teams { font-size: 1.1rem; font-weight: 600; color: #F2EFE6; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------- hero
st.markdown(f"""
<div class="hero-banner">
    <img src="{EMBLEM_URL}" alt="2026 FIFA World Cup emblem"/>
    <div>
        <p class="hero-title">⚽ World Cup Prediction Agent</p>
        <p class="hero-sub">2026 Edition — Canada · Mexico · USA</p>
        <p class="hero-caption">Optimized for your league: 5 exact · 3 result · −2 wrong winner
        (draws penalty-free) · +2 scorer</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------- match setup
with st.container(border=True):
    st.subheader("Match setup")
    c1, c2, c3 = st.columns([2, 2, 1])
    team_a = c1.selectbox("Team A", teams, index=teams.index("France") if "France" in teams else 0,
                           format_func=lambda t: f"{flag(t)} {t}")
    team_b = c2.selectbox("Team B", teams, index=teams.index("England") if "England" in teams else 1,
                           format_func=lambda t: f"{flag(t)} {t}")
    host = c3.selectbox("Host advantage", ["Neutral", team_a, team_b],
                         format_func=lambda t: t if t == "Neutral" else f"{flag(t)} {t}")

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

# ----------------------------------------------------------------- outlook
with st.container(border=True):
    st.subheader("Match outlook")
    st.markdown(f"""
    <div class="prob-bar-wrap">
        <div style="width:{p_a * 100:.2f}%; background:#3DDC97;"></div>
        <div style="width:{p_d * 100:.2f}%; background:#E8B339;"></div>
        <div style="width:{p_b * 100:.2f}%; background:#5AA9E8;"></div>
    </div>
    """, unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{flag(a)} {a} win", f"{p_a:.0%}")
    m2.metric("Draw", f"{p_d:.0%}")
    m3.metric(f"{flag(b)} {b} win", f"{p_b:.0%}")
    m4.metric("Expected goals", f"{mu_a:.2f} – {mu_b:.2f}")

# ----------------------------------------------------------------- recommendation
why = ("a draw pick carries zero penalty risk in your league"
       if s.score_a == s.score_b else
       "the result probability outweighs the wrong-winner risk")

with st.container(border=True):
    st.markdown(f"""
    <div class="rec-card">
        <img src="{TROPHY_URL}" alt="trophy"/>
        <span class="rec-teams">{flag(a)} {a}</span>
        <span class="rec-score"> {s.score_a} – {s.score_b} </span>
        <span class="rec-teams">{b} {flag(b)}</span>
    </div>
    """, unsafe_allow_html=True)
    st.write(f"Expected value **{s.ev:+.2f} pts** — exact-hit chance "
             f"{s.p_exact:.1%}, correct-result chance {s.p_result:.1%}; {why}.")
    if sc:
        st.write(f"**Scorer pick: {sc.player}** ({flag(sc.team)} {sc.team}) — "
                 f"{sc.p_scores:.0%} chance of scoring, worth {sc.ev:+.2f} pts of EV.")
    st.write(f"**Total expected points: {rec['expected_points']:.2f} / 7**")

# ----------------------------------------------------------------- alternatives
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("**Scoreline alternatives (by EV)**")
        alt = pd.DataFrame([{
            "Score": f"{x.score_a}–{x.score_b}",
            "EV (pts)": round(x.ev, 2),
            "P(exact)": f"{x.p_exact:.1%}",
            "Penalty risk": f"{x.p_opposite_win:.0%}",
        } for x in [s] + rec["scoreline_alternatives"]])
        st.dataframe(alt, hide_index=True, width='stretch')
with right:
    with st.container(border=True):
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
