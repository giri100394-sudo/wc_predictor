import ProbBar from './ProbBar'
import Flag from './Flag'
import { HIT_LABELS, HIT_STYLES } from '../utils'

const ACCENTS = {
  mint: { text: 'text-mint-600', bg: 'bg-mint-50', border: 'border-mint-500/30' },
  sky: { text: 'text-sky-600', bg: 'bg-sky-50', border: 'border-sky-500/30' },
}

export default function ModelPanel({ name, accent, data, home, away, played }) {
  const a = ACCENTS[accent]
  const { score, probs, p_exact, ev, outcome, points } = data

  return (
    <div className="rounded-xl border border-line bg-cloud-50/60 p-4 flex flex-col">
      <span className={`inline-block self-start text-xs font-bold tracking-wide px-3 py-1 rounded-full border ${a.bg} ${a.text} ${a.border}`}>
        {name}
      </span>

      <div className="font-display text-3xl text-ink-900 text-center my-2">
        {score[0]} – {score[1]}
      </div>

      <ProbBar home={probs.home} draw={probs.draw} away={probs.away} />

      <div className="grid grid-cols-3 text-center text-xs mt-2 gap-1">
        <div>
          <div className="text-ink-400 flex items-center justify-center gap-1">
            <Flag team={home} size="sm" /> win
          </div>
          <div className="font-semibold text-ink-900">{Math.round(probs.home * 100)}%</div>
        </div>
        <div>
          <div className="text-ink-400">Draw</div>
          <div className="font-semibold text-ink-900">{Math.round(probs.draw * 100)}%</div>
        </div>
        <div>
          <div className="text-ink-400 flex items-center justify-center gap-1">
            <Flag team={away} size="sm" /> win
          </div>
          <div className="font-semibold text-ink-900">{Math.round(probs.away * 100)}%</div>
        </div>
      </div>

      <div className="text-center text-[11px] text-ink-400 mt-2">
        P(exact) {Math.round(p_exact * 100)}% · EV {ev >= 0 ? '+' : ''}{ev.toFixed(2)} pts
      </div>

      {played && (
        <div className={`mt-2 text-center text-xs font-bold rounded-md py-1 ${HIT_STYLES[outcome]}`}>
          {HIT_LABELS[outcome]} ({points >= 0 ? '+' : ''}{points} pts)
        </div>
      )}
    </div>
  )
}
