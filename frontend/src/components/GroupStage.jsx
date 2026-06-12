import { useState } from 'react'
import Flag from './Flag'
import { formatDayParts, HIT_LABELS, HIT_STYLES } from '../utils'

const MODELS = [
  { key: 'poisson', name: 'Poisson', accent: 'text-mint-600' },
  { key: 'markov', name: 'Markov', accent: 'text-sky-600' },
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
    <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink-900 mb-1">Model performance</h2>

      {played.length === 0 ? (
        <p className="text-sm text-ink-400 mt-2">
          No results yet. As you fill in actual scores for World Cup matches (2026-06-11
          onward) in <span className="font-mono text-ink-700">data/sample_matches.csv</span>,
          this section will compare each model's pick against what actually happened.
        </p>
      ) : (
        <>
          <div className="overflow-x-auto -mx-2 mt-3">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
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
                    <tr key={key} className="border-t border-line">
                      <td className={`px-2 py-2 font-bold ${accent}`}>{name}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{played.length}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{avg.toFixed(2)}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{total}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{pct(played, 'exact', key)}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{pct(played, 'result', key)}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{pct(played, 'wrong_winner', key)}</td>
                      <td className="px-2 py-2 text-center text-ink-700">{pct(played, 'wrong', key)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <button
            onClick={() => setExpanded((e) => !e)}
            className="mt-4 text-sm font-semibold text-gold-600 hover:text-gold-500 cursor-pointer"
          >
            {expanded ? '▾' : '▸'} Match-by-match results ({played.length} played)
          </button>

          {expanded && (
            <div className="overflow-x-auto -mx-2 mt-3">
              <table className="w-full text-sm min-w-[720px]">
                <thead>
                  <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                    <th className="px-2 py-2 font-semibold">Date</th>
                    <th className="px-2 py-2 font-semibold">Match</th>
                    <th className="px-2 py-2 font-semibold text-center">Actual</th>
                    <th className="px-2 py-2 font-semibold text-center text-mint-600">Poisson</th>
                    <th className="px-2 py-2 font-semibold text-center text-sky-600">Markov</th>
                  </tr>
                </thead>
                <tbody>
                  {played.map((f) => {
                    const { day, month } = formatDayParts(f.date)
                    return (
                      <tr key={f.id} className="border-t border-line">
                        <td className="px-2 py-2 whitespace-nowrap text-ink-700">{day} {month}</td>
                        <td className="px-2 py-2 whitespace-nowrap text-ink-900">
                          <span className="inline-flex items-center gap-1.5">
                            <Flag team={f.home_team} size="sm" /> {f.home_team} vs {f.away_team} <Flag team={f.away_team} size="sm" />
                          </span>
                        </td>
                        <td className="px-2 py-2 text-center font-semibold text-ink-900">
                          {f.actual.home}-{f.actual.away}
                        </td>
                        {MODELS.map(({ key }) => {
                          const m = f.models[key]
                          return (
                            <td key={key} className="px-2 py-2 text-center whitespace-nowrap">
                              <div className="text-ink-900">{m.score[0]}-{m.score[1]}</div>
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
