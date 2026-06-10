# World Cup Prediction-League Agent

Predicts scorelines and goalscorers optimized for your league's exact points
system — it doesn't predict the *most likely* outcome, it predicts the
*highest expected points* outcome.

## The rules it optimizes for

| Outcome | Points |
|---|---|
| Exact scoreline | 5 |
| Correct result only | 3 |
| Wrong winner (predicted win, other team won) | −2 |
| Predicted draw, any wrong outcome | 0 |
| Picked player scores | +2 |

Two strategic consequences are baked into the optimizer:

1. **Draws are penalty-free**, so in close matches (~within 33/33/33) a 1-1
   prediction usually beats backing either side, even when a draw isn't the
   most likely result.
2. **The scorer pick is independent** of your scoreline, so it always picks
   the highest P(scores ≥ 1) from *either* team.

## Quick start

```bash
pip install pandas numpy scipy

# generate sample data (or drop in real data, see below)
python data/generate_sample_data.py   # run from data/

# predict a match
python src/predict.py "France" "England"
python src/predict.py "USA" "Ecuador" --host USA   # host gets home advantage
```

## Project layout

```
data/
  generate_sample_data.py   synthetic-but-realistic match history
  sample_matches.csv        2,500 matches (replace with real data)
  sample_players.csv        player goal shares / start probabilities
src/
  poisson_model.py          fits attack/defense strengths (time-decayed MLE)
  ev_optimizer.py           your league rules → expected-value rankings
  predict.py                CLI report
  agent.py                  LLM wrapper (Anthropic API) that layers context
                            like injuries on top of the statistical output
```

## Swapping in real data (do this before the tournament!)

**Matches:** the sample CSV matches the format of the Kaggle dataset
"International football results from 1872 to 2017" (`results.csv`, updated
continuously). Download it and point at it:

```bash
python src/predict.py "Spain" "Brazil" --matches data/results.csv
```

**Players:** edit `data/sample_players.csv`. For each player you need:
- `goal_share` — their fraction of the team's goals over the last ~2 years
  (compute from FBref international stats)
- `p_start` — probability they start / play meaningful minutes
- `minutes_frac` — expected fraction of the match played

Update `p_start` before each match once lineups leak (~1h before kickoff,
still before the lock).

## The agent layer

`src/agent.py` wraps the model as a tool for Claude, which adjusts for things
the statistics can't see — injuries, rotation after a team has already
qualified, motivation. Requires `pip install anthropic` and an
`ANTHROPIC_API_KEY` env var:

```bash
python src/agent.py "France" "England" --context "Mbappé doubtful (ankle knock)"
```

## Upgrade ideas, in rough order of value

1. **Real data** — biggest single improvement, costs nothing.
2. **Dixon-Coles correction** — Poisson underrates 0-0 and 1-1; since your
   league makes draws extra valuable, this correction directly earns points.
3. **Knockout-stage handling** — decide whether your league scores 90-minute
   results or final results, and adjust the draw logic accordingly.
4. **Lineup-aware scorer picks** — scrape confirmed lineups pre-kickoff and
   set `p_start` to 1 or 0.
5. **Leaderboard-aware risk** — if you're trailing late in the tournament,
   deliberately pick higher-variance exact scores instead of max-EV ones.

## Calibration warning

Even strong models call ~55-60% of match results correctly. The edge here is
not clairvoyance — it's consistently making +EV picks under your scoring rules
while opponents pick on gut feel. Over ~70 matches, that compounds.

## Web UI

```bash
pip install streamlit
streamlit run app.py
```

Opens in your browser at http://localhost:8501 with three tabs:
**Predict** (pick teams, see EV-ranked recommendations, save your pick),
**Log result** (enter the real score after the whistle), and
**Feedback report** (your points, hit rates, and data-driven refinement hints).

## Putting it on GitHub

1. Create a free account at github.com, click **New repository**, name it
   (e.g. `wc-prediction-agent`), keep it Public or Private, do NOT initialize
   with a README (you already have one).
2. Install GitHub Desktop (desktop.github.com) — easiest on Windows.
3. In GitHub Desktop: File → Add local repository → choose your wc_predictor
   folder → "create a repository" when prompted → Publish repository.
4. Future changes: edit files, write a summary in GitHub Desktop, Commit,
   then Push.

The included .gitignore keeps your personal prediction logs out of the repo.
