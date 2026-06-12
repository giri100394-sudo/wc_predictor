import { flag } from '../flags'

export default function ScorerChips({ scorers }) {
  return (
    <div className="mt-4">
      <div className="text-xs font-semibold text-white/45 uppercase tracking-wide mb-2">
        Top scorer picks
      </div>
      {scorers && scorers.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {scorers.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3 py-1.5 text-sm"
            >
              <span>{flag(s.team)}</span>
              <span className="font-medium">{s.player}</span>
              <span className="text-gold-400 font-bold">{s.probability_pct}%</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-white/40">
          No player data available for these teams yet.
        </div>
      )}
    </div>
  )
}
