"""
Web-based "player to score" predictions.

Instead of relying on the static data/sample_players.csv squad sheet, this
module asks Claude (with the web search tool) to look up current
goalscorer odds and prediction-provider previews (Opta, bookmakers, pundit
previews, etc.) for a fixture and return the 3 players most likely to score.

Results are cached to disk under data/scorer_cache/ — each lookup costs a
real API call with several web searches, so the API layer should treat this
as "pre-computed", not "call on every page load":

    - get_top_scorers(team_a, team_b)            -> cached result, or None
    - get_top_scorers(team_a, team_b, fetch_live=True) -> calls the API if
      there's no fresh cache entry

To populate the cache for every World Cup 2026 fixture ahead of time:

    ANTHROPIC_API_KEY=... python src/scorer_agent.py --refresh

Falls back to None (caller should fall back to the statistical
scorer_evs() estimate) if ANTHROPIC_API_KEY is missing, the lookup fails,
or the response can't be parsed.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "scorer_cache"
CACHE_TTL_HOURS = 24

MODEL = "claude-sonnet-4-5-20250929"

SYSTEM = """You are a football analyst sourcing anytime-goalscorer predictions for a
FIFA World Cup 2026 group-stage fixture.

Use web search to find current goalscorer odds, recent goal-scoring form, and
prediction-provider previews (e.g. Opta's predicted lineups/scorers, bookmaker
anytime-scorer odds, pundit match previews) for both teams in the fixture.

Pick the 3 players (from either team, combined) most likely to score in this
match, and estimate each one's probability of scoring at least once, as a
number from 0 to 100.

Do your research first, then finish your reply with a fenced code block
containing ONLY a JSON array of exactly 3 objects, using EXACTLY these keys
(no extra keys, no missing keys):
  "player"           - full player name (string)
  "team"             - the team they play for; must exactly match one of the
                       two team names given in the prompt (string)
  "probability_pct"  - your estimated chance they score, 0-100 (number)
  "source"           - short note on where this estimate came from, e.g.
                       "Opta predicted lineup" or "bookmaker anytime scorer odds"

Example final block:
```json
[
  {"player": "Kylian Mbappe", "team": "France", "probability_pct": 55.0, "source": "bookmaker anytime scorer odds"},
  {"player": "Ousmane Dembele", "team": "France", "probability_pct": 32.0, "source": "Opta predicted lineup"},
  {"player": "Erling Haaland", "team": "Norway", "probability_pct": 60.0, "source": "recent goalscoring form"}
]
```
"""


def _cache_path(team_a: str, team_b: str) -> Path:
    key = hashlib.sha1(f"{team_a}|{team_b}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json"


def _read_cache(team_a: str, team_b: str) -> list[dict] | None:
    path = _cache_path(team_a, team_b)
    if not path.exists():
        return None
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    if age_hours > CACHE_TTL_HOURS:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_cache(team_a: str, team_b: str, data: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(team_a, team_b).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _extract_json(text: str) -> list[dict] | None:
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    start, end = candidate.find("["), candidate.rfind("]")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(candidate[start:end + 1])
    except ValueError:
        return None
    if not isinstance(data, list):
        return None
    out = []
    for item in data:
        if not isinstance(item, dict) or "player" not in item or "team" not in item:
            continue
        out.append({
            "player": str(item["player"]),
            "team": str(item["team"]),
            "probability_pct": round(float(item.get("probability_pct", 0)), 1),
            "source": str(item.get("source", "")),
        })
    return out or None


def _fetch_live(team_a: str, team_b: str) -> list[dict] | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    prompt = (
        f"Fixture: {team_a} vs {team_b} at the FIFA World Cup 2026 "
        f"(group stage, June 2026). Find the 3 most likely goalscorers."
    )
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return None

    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return _extract_json(text)


def get_top_scorers(team_a: str, team_b: str, use_cache: bool = True,
                     fetch_live: bool = False) -> list[dict] | None:
    """3 most likely goalscorers for `team_a vs team_b`, sourced from the web.

    Returns None (caller falls back to the statistical estimate) if no cached
    result exists and `fetch_live` is False, or if the live lookup fails.
    """
    if use_cache:
        cached = _read_cache(team_a, team_b)
        if cached is not None:
            return cached
    if not fetch_live:
        return None

    data = _fetch_live(team_a, team_b)
    if data:
        _write_cache(team_a, team_b, data)
    return data


# kept for backwards-compat with api/main.py's import name
web_top_scorers = get_top_scorers


if __name__ == "__main__":
    import argparse

    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matches", default=str(ROOT / "data" / "sample_matches.csv"))
    ap.add_argument("--refresh", action="store_true",
                    help="populate the cache for every WC2026 fixture")
    ap.add_argument("--force", action="store_true",
                    help="re-fetch even if a fresh cache entry exists")
    ap.add_argument("team_a", nargs="?")
    ap.add_argument("team_b", nargs="?")
    args = ap.parse_args()

    if args.refresh:
        df = pd.read_csv(args.matches, encoding="utf-8")
        df["date"] = pd.to_datetime(df["date"])
        wc = df[(df["date"] >= "2026-06-11") & (df["tournament"] == "FIFA World Cup")]
        for _, m in wc.iterrows():
            a, b = m.home_team, m.away_team
            print(f"{a} vs {b} ...", end=" ", flush=True)
            result = get_top_scorers(a, b, use_cache=not args.force, fetch_live=True)
            print("ok" if result else "skip/fail")
    elif args.team_a and args.team_b:
        print(json.dumps(get_top_scorers(args.team_a, args.team_b, use_cache=False,
                                          fetch_live=True), indent=2))
    else:
        ap.error("specify --refresh, or a team_a/team_b pair")
