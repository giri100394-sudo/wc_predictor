import Flag from './Flag'
import ModelPanel from './ModelPanel'
import ScorerChips from './ScorerChips'

export default function MatchCard({ fixture, index }) {
  const { home_team, away_team, venue, actual, models, top_scorers } = fixture
  const played = actual !== null

  return (
    <div
      className="animate-fade-in-up rounded-2xl border border-line bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
      style={{ animationDelay: `${Math.min(index * 0.04, 0.4)}s` }}
    >
      <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
        <div className="flex items-center gap-2 text-lg font-bold text-ink-900">
          <Flag team={home_team} size="lg" />
          <span>{home_team}</span>
          <span className="text-ink-400 font-normal text-sm">vs</span>
          <span>{away_team}</span>
          <Flag team={away_team} size="lg" />
        </div>
        <span className="text-xs text-ink-400">{venue}</span>
      </div>

      {played && (
        <div className="flex items-center justify-center gap-2 my-3 rounded-lg bg-gold-50 border border-gold-500/30 text-ink-900 font-semibold py-2">
          <span>Final score:</span>
          <Flag team={home_team} size="sm" />
          <span>{actual.home} – {actual.away}</span>
          <Flag team={away_team} size="sm" />
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
