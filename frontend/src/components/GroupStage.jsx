import { useState } from 'react'
import { flag } from '../flags'
import { formatDayParts, HIT_LABELS, HIT_STYLES } from '../utils'

const MODELS = [
  { key: 'poisson', name: 'Poisson', accent: 'text-mint-400' },
  { key: 'markov', name: 'Markov', accent: 'text-sky-400' },
]

function pct(played, outcome, key) {
  if (played.length === 0) return '0%'
  const n = played.filter((f) => f.models[key].outcome === outcome).length
  return `${Math.round((n / played.length) * 100)}%`
}

export default function GroupStage({ fixtures }) {
  const [expanded, setExpanded] = useState(false)
  const played = fixtures.filter((f) => f.actual !== null)

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
      <h2 className="text-lg font-bold mb-1">Group stage so far</h2>

      {played.length === 0 ? (
        <p className="text-sm text-white/60 mt-2">
          No results yet. As you fill in actual scores for World Cup matches (2026-06-11
          onward) in <span className="font-mono text-white/80">data/sample_matches.csv</span>,
          this section will compare each model's pick against what actually happened.
        </p>
      ) : (
        <>
          <div className="overflow-x-auto -mx-2 mt-3">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left text-white/45 text-xs uppercase tracking-wide">
                  <th className="px-2 py-2 font-semibold">Model</th>
                  <th className="px-2 py-2 font-semibold text-center">Matches</th>
                  <th className="px-2 py-2 font-semibold text-center">Avg pts/match</th>
                  <th className="px-2 py-2 font-semibold text-center">Total pts</th>
                  <th className="px-2 py-2 font-semibold text-center">Exact</th>
                  <th className="px-2 py-2 font-semibold text-center">Result</th>
                  <th className="px-2 py-2 font-semibold text-center">Wrong winner</th>
                  <th className="px-2 py-2 font-semibold text-center">Wrong</th>
                </tr>
              </thead>
              <tbody>
                {MODELS.map(({ key, name, accent }) => {
                  const pts = played.map((f) => f.models[key].points)
                  const total = pts.reduce((a, b) => a + b, 0)
                  const avg = total / played.length
                  return (
                    <tr key={key} className="border-t border-white/5">
                      <td className={`px-2 py-2 font-bold ${accent}`}>{name}</td>
                      <td className="px-2 py-2 text-center">{played.length}</td>
                      <td className="px-2 py-2 text-center">{avg.toFixed(2)}</td>
                      <td className="px-2 py-2 text-center">{total}</td>
                      <td className="px-2 py-2 text-center">{pct(played, 'exact', key)}</td>
                      <td className="px-2 py-2 text-center">{pct(played, 'result', key)}</td>
                      <td className="px-2 py-2 text-center">{pct(played, 'wrong_winner', key)}</td>
                      <td className="px-2 py-2 text-center">{pct(played, 'wrong', key)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <button
            onClick={() => setExpanded((e) => !e)}
            className="mt-4 text-sm font-semibold text-gold-400 hover:text-gold-500 cursor-pointer"
          >
            {expanded ? '▾' : '▸'} Match-by-match results ({played.length} played)
          </button>

          {expanded && (
            <div className="overflow-x-auto -mx-2 mt-3">
              <table className="w-full text-sm min-w-[720px]">
                <thead>
                  <tr className="text-left text-white/45 text-xs uppercase tracking-wide">
                    <th className="px-2 py-2 font-semibold">Date</th>
                    <th className="px-2 py-2 font-semibold">Match</th>
                    <th className="px-2 py-2 font-semibold text-center">Actual</th>
                    <th className="px-2 py-2 font-semibold text-center text-mint-400">Poisson</th>
                    <th className="px-2 py-2 font-semibold text-center text-sky-400">Markov</th>
                  </tr>
                </thead>
                <tbody>
                  {played.map((f) => {
                    const { day, month } = formatDayParts(f.date)
                    return (
                      <tr key={f.id} className="border-t border-white/5">
                        <td className="px-2 py-2 whitespace-nowrap text-white/70">{day} {month}</td>
                        <td className="px-2 py-2 whitespace-nowrap">
                          {flag(f.home_team)} {f.home_team} vs {f.away_team} {flag(f.away_team)}
                        </td>
                        <td className="px-2 py-2 text-center font-semibold">
                          {f.actual.home}-{f.actual.away}
                        </td>
                        {MODELS.map(({ key }) => {
                          const m = f.models[key]
                          return (
                            <td key={key} className="px-2 py-2 text-center whitespace-nowrap">
                              <div>{m.score[0]}-{m.score[1]}</div>
                              <span className={`inline-block mt-0.5 text-[10px] font-bold rounded px-1.5 py-0.5 ${HIT_STYLES[m.outcome]}`}>
                                {HIT_LABELS[m.outcome]} ({m.points >= 0 ? '+' : ''}{m.points})
                              </span>
                            </td>
                          )
                        })}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
