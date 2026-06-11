"""
World Cup 2026 Prediction Agent — single-page web UI.

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
from markov_model import MarkovModel
from ev_optimizer import scoreline_evs, scorer_evs
from tracker import score_prediction

MATCHES_CSV = ROOT / "data" / "sample_matches.csv"
PLAYERS_CSV = ROOT / "data" / "sample_players.csv"

WC_START = "2026-06-11"
WC_TOURNAMENT = "FIFA World Cup"

EMBLEM_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/"
               "2026_FIFA_World_Cup_emblem.svg/250px-2026_FIFA_World_Cup_emblem.svg.png")
TROPHY_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/"
              "Golden_trophy.svg/250px-Golden_trophy.svg.png")

FLAGS = {
    "Algeria": "🇩🇿", "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪", "Bosnia and Herzegovina": "🇧🇦", "Brazil": "🇧🇷",
    "Canada": "🇨🇦", "Cape Verde": "🇨🇻", "Colombia": "🇨🇴", "Costa Rica": "🇨🇷",
    "Croatia": "🇭🇷", "Curaçao": "🇨🇼", "Czech Republic": "🇨🇿", "Denmark": "🇩🇰",
    "DR Congo": "🇨🇩", "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France": "🇫🇷", "Germany": "🇩🇪", "Ghana": "🇬🇭", "Haiti": "🇭🇹",
    "Iran": "🇮🇷", "Iraq": "🇮🇶", "Italy": "🇮🇹", "Ivory Coast": "🇨🇮",
    "Japan": "🇯🇵", "Jordan": "🇯🇴", "Mexico": "🇲🇽", "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Norway": "🇳🇴", "Panama": "🇵🇦",
    "Paraguay": "🇵🇾", "Poland": "🇵🇱", "Portugal": "🇵🇹", "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳", "Serbia": "🇷🇸",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸", "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭", "Tunisia": "🇹🇳", "Turkey": "🇹🇷", "United States": "🇺🇸",
    "USA": "🇺🇸", "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿",
}

# the players sample CSV may use a different name for the same team
PLAYER_TEAM_ALIASES = {"United States": "USA", "USA": "United States"}


def flag(team: str) -> str:
    return FLAGS.get(team, "🏳️")


def team_players(players_df: pd.DataFrame, team: str) -> list[dict]:
    names = {team, PLAYER_TEAM_ALIASES.get(team, team)}
    return players_df[players_df["team"].isin(names)].to_dict("records")


def result_probs(grid: np.ndarray) -> tuple[float, float, float]:
    p_a = float(np.tril(grid, -1).sum())
    p_d = float(np.trace(grid))
    p_b = float(np.triu(grid, 1).sum())
    return p_a, p_d, p_b


def outcome_label(score_a: int, score_b: int) -> str:
    if score_a > score_b:
        return "1"
    if score_a < score_b:
        return "2"
    return "X"


HIT_LABELS = {"exact": "Exact", "result": "Result", "wrong_winner": "Wrong winner", "wrong": "Wrong"}


st.set_page_config(page_title="WC Prediction Agent", page_icon="⚽", layout="wide")


# ----------------------------------------------------------------- caching
@st.cache_resource(show_spinner="Fitting models on match history…")
def get_models(matches_path: str, mtime: float) -> tuple[PoissonModel, MarkovModel]:
    df = pd.read_csv(matches_path)
    return PoissonModel().fit(df), MarkovModel().fit(df)


@st.cache_data
def get_players(players_path: str) -> pd.DataFrame:
    return pd.read_csv(players_path)


@st.cache_data
def load_fixtures(matches_path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(matches_path)
    df["date"] = pd.to_datetime(df["date"])
    wc = df[(df["date"] >= WC_START) & (df["tournament"] == WC_TOURNAMENT)]
    return wc.sort_values("date").reset_index(drop=True)


mtime = MATCHES_CSV.stat().st_mtime
poisson, markov = get_models(str(MATCHES_CSV), mtime)
players_df = get_players(str(PLAYERS_CSV))
fixtures = load_fixtures(str(MATCHES_CSV), mtime)
known = set(poisson.attack) & set(markov.pi)
fixtures = fixtures[fixtures["home_team"].isin(known) & fixtures["away_team"].isin(known)]

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
    display: flex; height: 12px; border-radius: 8px; overflow: hidden;
    margin: 0.5rem 0 0.7rem 0; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

.model-pill {
    display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
    font-weight: 700; font-size: 0.78rem; margin-bottom: 0.5rem; letter-spacing: 0.03em;
}
.model-pill.poisson { background: rgba(61,220,151,0.16); color: #3DDC97; border: 1px solid rgba(61,220,151,0.4); }
.model-pill.markov { background: rgba(90,169,232,0.16); color: #5AA9E8; border: 1px solid rgba(90,169,232,0.4); }

.score-big {
    font-size: 2rem; font-weight: 800; color: #E8B339; text-align: center; margin: 0.1rem 0 0.3rem 0;
}

.hit-pill {
    display: inline-block; padding: 0.12rem 0.6rem; border-radius: 6px;
    font-size: 0.78rem; font-weight: 700; margin-top: 0.3rem;
}
.hit-pill.exact { background: #3DDC97; color: #0E4D32; }
.hit-pill.result { background: #E8B339; color: #16291F; }
.hit-pill.wrong_winner { background: #E07A5F; color: #fff; }
.hit-pill.wrong { background: #555; color: #fff; }

.actual-banner {
    text-align: center; font-weight: 700; color: #F2EFE6;
    background: rgba(232,179,57,0.14); border: 1px solid rgba(232,179,57,0.35);
    border-radius: 10px; padding: 0.35rem; margin-bottom: 0.7rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------- hero
st.markdown(f"""
<div class="hero-banner">
    <img src="{EMBLEM_URL}" alt="2026 FIFA World Cup emblem"/>
    <div>
        <p class="hero-title">⚽ World Cup 2026 Prediction Agent</p>
        <p class="hero-sub">Group Stage — 11 to 27 June · Canada · Mexico · USA</p>
        <p class="hero-caption">Poisson and Markov-chain models, optimized for your league: 5 exact ·
        3 result · −2 wrong winner (draws penalty-free) · +2 scorer</p>
    </div>
</div>
""", unsafe_allow_html=True)

if fixtures.empty:
    st.warning("No FIFA World Cup fixtures from 2026-06-11 onward found in "
               "data/sample_matches.csv.")
    st.stop()

played = fixtures.dropna(subset=["home_score", "away_score"])
upcoming = fixtures[fixtures["home_score"].isna()]

# ----------------------------------------------------------------- group stage so far
with st.container(border=True):
    st.subheader("Group stage so far")
    if played.empty:
        st.info("No results yet. As you fill in actual scores for World Cup matches "
                "(2026-06-11 onward) in **data/sample_matches.csv**, this section will "
                "compare each model's pick against what actually happened.")
    else:
        rows = []
        for _, m in played.iterrows():
            a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
            actual_a, actual_b = int(m.home_score), int(m.away_score)
            row = {"Date": m.date.date(), "Home": a, "Away": b,
                   "Actual": f"{actual_a}-{actual_b}"}
            for name, model in [("Poisson", poisson), ("Markov", markov)]:
                grid = model.score_grid(a, b, neutral=neutral)
                pick = scoreline_evs(grid)[0]
                sc = score_prediction(pick.score_a, pick.score_b, actual_a, actual_b, False)
                row[f"{name} pick"] = f"{pick.score_a}-{pick.score_b}"
                row[f"{name} outcome"] = sc["outcome"]
                row[f"{name} pts"] = sc["scoreline_points"]
            rows.append(row)
        comp = pd.DataFrame(rows)

        n = len(comp)
        summary = pd.DataFrame([
            {
                "Model": name,
                "Matches": n,
                "Avg pts/match": round(comp[f"{name} pts"].mean(), 2),
                "Total pts": int(comp[f"{name} pts"].sum()),
                "Exact": f"{(comp[f'{name} outcome'] == 'exact').mean():.0%}",
                "Result": f"{(comp[f'{name} outcome'] == 'result').mean():.0%}",
                "Wrong winner": f"{(comp[f'{name} outcome'] == 'wrong_winner').mean():.0%}",
                "Wrong": f"{(comp[f'{name} outcome'] == 'wrong').mean():.0%}",
            }
            for name in ["Poisson", "Markov"]
        ]).set_index("Model")
        st.dataframe(summary, width='stretch')

        with st.expander(f"Match-by-match results ({n} played)"):
            display_cols = ["Date", "Home", "Away", "Actual",
                             "Poisson pick", "Poisson outcome", "Poisson pts",
                             "Markov pick", "Markov outcome", "Markov pts"]
            st.dataframe(comp[display_cols], hide_index=True, width='stretch')

# ----------------------------------------------------------------- all fixtures table
with st.container(border=True):
    st.subheader("All fixtures")
    st.caption("Each model's pick is its highest expected-value scoreline under your "
               "league's scoring rules. 1 = home win, X = draw, 2 = away win.")
    rows = []
    for _, m in fixtures.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        row = {
            "Date": m.date.date(),
            "Match": f"{flag(a)} {a} vs {b} {flag(b)}",
            "Venue": "Neutral" if neutral else f"{a} (host)",
            "Result": (f"{int(m.home_score)}-{int(m.away_score)}"
                       if pd.notna(m.home_score) else "—"),
        }
        for name, model in [("Poisson", poisson), ("Markov", markov)]:
            grid = model.score_grid(a, b, neutral=neutral)
            pick = scoreline_evs(grid)[0]
            row[name] = f"{pick.score_a}-{pick.score_b} ({outcome_label(pick.score_a, pick.score_b)})"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch', height=320)

# ----------------------------------------------------------------- matchday browser
with st.container(border=True):
    st.subheader("Browse by matchday")

    dates = sorted(fixtures["date"].dt.date.unique())
    counts = fixtures.groupby(fixtures["date"].dt.date).size()
    sel = st.selectbox(
        "Matchday", options=range(len(dates)),
        format_func=lambda i: f"{dates[i].strftime('%a %d %b %Y')} — {counts[dates[i]]} matches",
    )
    day = dates[sel]
    day_matches = fixtures[fixtures["date"].dt.date == day]

    for _, m in day_matches.iterrows():
        a, b, neutral = m.home_team, m.away_team, bool(m.neutral)
        is_played = pd.notna(m.home_score)
        actual_a, actual_b = (int(m.home_score), int(m.away_score)) if is_played else (None, None)
        venue = "Neutral venue" if neutral else f"{flag(a)} {a} (host)"

        with st.container(border=True):
            st.markdown(f"#### {flag(a)} {a}  vs  {b} {flag(b)}")
            st.caption(f"{m.date.strftime('%A %d %B %Y')} · {venue}")
            if is_played:
                st.markdown(f'<div class="actual-banner">Final score: '
                             f'{flag(a)} {a} {actual_a} – {actual_b} {b} {flag(b)}</div>',
                             unsafe_allow_html=True)

            cols = st.columns(2)
            for col, name, css_class, model in [
                (cols[0], "Poisson", "poisson", poisson),
                (cols[1], "Markov", "markov", markov),
            ]:
                with col:
                    st.markdown(f'<span class="model-pill {css_class}">{name}</span>',
                                 unsafe_allow_html=True)
                    grid = model.score_grid(a, b, neutral=neutral)
                    pick = scoreline_evs(grid)[0]
                    p_a, p_d, p_b = result_probs(grid)

                    st.markdown(f'<div class="score-big">{pick.score_a} – {pick.score_b}</div>',
                                 unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="prob-bar-wrap">
                        <div style="width:{p_a * 100:.2f}%; background:#3DDC97;"></div>
                        <div style="width:{p_d * 100:.2f}%; background:#E8B339;"></div>
                        <div style="width:{p_b * 100:.2f}%; background:#5AA9E8;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"{flag(a)} win", f"{p_a:.0%}")
                    m2.metric("Draw", f"{p_d:.0%}")
                    m3.metric(f"{flag(b)} win", f"{p_b:.0%}")
                    st.caption(f"P(exact) {pick.p_exact:.0%} · EV {pick.ev:+.2f} pts")

                    if is_played:
                        sc = score_prediction(pick.score_a, pick.score_b,
                                               actual_a, actual_b, False)
                        st.markdown(
                            f'<span class="hit-pill {sc["outcome"]}">'
                            f'{HIT_LABELS[sc["outcome"]]} ({sc["scoreline_points"]:+d} pts)</span>',
                            unsafe_allow_html=True)

            mu_a, mu_b = poisson.expected_goals(a, b, neutral=neutral)
            pa = team_players(players_df, a)
            pb = team_players(players_df, b)
            top3 = scorer_evs(mu_a, mu_b, pa, pb)[:3]
            st.markdown("**Top scorer picks**")
            if top3:
                sc_cols = st.columns(len(top3))
                for c, sc in zip(sc_cols, top3):
                    c.metric(f"{flag(sc.team)} {sc.player}", f"{sc.p_scores:.0%}")
            else:
                st.caption("No player data available for these teams yet — "
                           "add rows to data/sample_players.csv.")
