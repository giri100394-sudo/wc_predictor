import { flag } from '../flags'
import ProbBar from './ProbBar'
import { HIT_LABELS, HIT_STYLES } from '../utils'

const ACCENTS = {
  mint: { text: 'text-mint-400', bg: 'bg-mint-500/15', border: 'border-mint-500/40' },
  sky: { text: 'text-sky-400', bg: 'bg-sky-500/15', border: 'border-sky-500/40' },
}

export default function ModelPanel({ name, accent, data, home, away, played }) {
  const a = ACCENTS[accent]
  const { score, probs, p_exact, ev, outcome, points } = data

  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4 flex flex-col">
      <span className={`inline-block self-start text-xs font-bold tracking-wide px-3 py-1 rounded-full border ${a.bg} ${a.text} ${a.border}`}>
        {name}
      </span>

      <div className="font-display text-3xl text-gold-400 text-center my-2">
        {score[0]} – {score[1]}
      </div>

      <ProbBar home={probs.home} draw={probs.draw} away={probs.away} />

      <div className="grid grid-cols-3 text-center text-xs mt-2 gap-1">
        <div>
          <div className="text-white/45">{flag(home)} win</div>
          <div className="font-semibold">{Math.round(probs.home * 100)}%</div>
        </div>
        <div>
          <div className="text-white/45">Draw</div>
          <div className="font-semibold">{Math.round(probs.draw * 100)}%</div>
        </div>
        <div>
          <div className="text-white/45">{flag(away)} win</div>
          <div className="font-semibold">{Math.round(probs.away * 100)}%</div>
        </div>
      </div>

      <div className="text-center text-[11px] text-white/40 mt-2">
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
