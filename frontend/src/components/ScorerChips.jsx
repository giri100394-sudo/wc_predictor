import Flag from './Flag'

export default function ScorerChips({ scorers }) {
  return (
    <div className="mt-4">
      <div className="text-xs font-semibold text-ink-400 uppercase tracking-wide mb-2">
        Top scorer picks
      </div>
      {scorers && scorers.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {scorers.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-2 rounded-full bg-cloud-50 border border-line px-3 py-1.5 text-sm"
            >
              <Flag team={s.team} size="sm" />
              <span className="font-medium text-ink-900">{s.player}</span>
              <span className="text-gold-600 font-bold">{s.probability_pct}%</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-ink-400">
          No player data available for these teams yet.
        </div>
      )}
    </div>
  )
}
