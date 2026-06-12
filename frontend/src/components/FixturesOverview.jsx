import { flag } from '../flags'
import { outcomeLabel, formatDayParts } from '../utils'

export default function FixturesOverview({ fixtures }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
      <h2 className="text-lg font-bold mb-1">All fixtures</h2>
      <p className="text-xs text-white/45 mb-4">
        Each model's pick is its highest expected-value scoreline under your league's
        scoring rules. 1 = home win, X = draw, 2 = away win.
      </p>

      <div className="overflow-x-auto -mx-2">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-left text-white/45 text-xs uppercase tracking-wide">
              <th className="px-2 py-2 font-semibold">Date</th>
              <th className="px-2 py-2 font-semibold">Match</th>
              <th className="px-2 py-2 font-semibold">Venue</th>
              <th className="px-2 py-2 font-semibold text-center">Result</th>
              <th className="px-2 py-2 font-semibold text-center text-mint-400">Poisson</th>
              <th className="px-2 py-2 font-semibold text-center text-sky-400">Markov</th>
            </tr>
          </thead>
          <tbody>
            {fixtures.map((f) => {
              const { day, month } = formatDayParts(f.date)
              const poisson = f.models.poisson
              const markov = f.models.markov
              return (
                <tr key={f.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-2 py-2 whitespace-nowrap text-white/70">{day} {month}</td>
                  <td className="px-2 py-2 whitespace-nowrap">
                    {flag(f.home_team)} {f.home_team} vs {f.away_team} {flag(f.away_team)}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-white/50">{f.venue}</td>
                  <td className="px-2 py-2 text-center font-semibold">
                    {f.actual ? `${f.actual.home}-${f.actual.away}` : '—'}
                  </td>
                  <td className="px-2 py-2 text-center whitespace-nowrap">
                    {poisson.score[0]}-{poisson.score[1]}
                    <span className="text-white/40"> ({outcomeLabel(poisson.score[0], poisson.score[1])})</span>
                  </td>
                  <td className="px-2 py-2 text-center whitespace-nowrap">
                    {markov.score[0]}-{markov.score[1]}
                    <span className="text-white/40"> ({outcomeLabel(markov.score[0], markov.score[1])})</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
