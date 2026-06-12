import { flag } from '../flags'
import ModelPanel from './ModelPanel'
import ScorerChips from './ScorerChips'

export default function MatchCard({ fixture, index }) {
  const { home_team, away_team, venue, actual, models, top_scorers } = fixture
  const played = actual !== null

  return (
    <div
      className="animate-fade-in-up rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 shadow-xl shadow-black/20"
      style={{ animationDelay: `${Math.min(index * 0.04, 0.4)}s` }}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2 text-lg font-bold">
          <span>{flag(home_team)}</span>
          <span>{home_team}</span>
          <span className="text-white/40 font-normal">vs</span>
          <span>{away_team}</span>
          <span>{flag(away_team)}</span>
        </div>
        <span className="text-xs text-white/40">{venue}</span>
      </div>

      {played && (
        <div className="text-center my-3 rounded-lg bg-gold-500/15 border border-gold-500/30 text-gold-400 font-semibold py-2">
          Final score: {flag(home_team)} {actual.home} – {actual.away} {flag(away_team)}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
        <ModelPanel
          name="Poisson"
          accent="mint"
          data={models.poisson}
          home={home_team}
          away={away_team}
          played={played}
        />
        <ModelPanel
          name="Markov"
          accent="sky"
          data={models.markov}
          home={home_team}
          away={away_team}
          played={played}
        />
      </div>

      <ScorerChips scorers={top_scorers} />
    </div>
  )
}
