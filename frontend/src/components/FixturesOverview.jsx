import Flag from './Flag'
import { outcomeLabel, formatDayParts } from '../utils'
import matchBallsImg from '../assets/match-balls.webp'

export default function FixturesOverview({ fixtures }) {
  return (
    <div className="rounded-2xl border border-line bg-white shadow-sm overflow-hidden">
      <img src={matchBallsImg} alt="" className="w-full h-28 sm:h-36 object-cover" />

      <div className="p-5">
      <h2 className="text-lg font-bold text-ink-900 mb-1">All fixtures</h2>
      <p className="text-xs text-ink-400 mb-4">
        Each model's pick is its highest expected-value scoreline under your league's
        scoring rules. 1 = home win, X = draw, 2 = away win.
      </p>

      <div className="overflow-x-auto -mx-2">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
              <th className="px-2 py-2 font-semibold">Date</th>
              <th className="px-2 py-2 font-semibold">Match</th>
              <th className="px-2 py-2 font-semibold">Venue</th>
              <th className="px-2 py-2 font-semibold text-center">Result</th>
              <th className="px-2 py-2 font-semibold text-center text-mint-600">Poisson</th>
              <th className="px-2 py-2 font-semibold text-center text-sky-600">Markov</th>
            </tr>
          </thead>
          <tbody>
            {fixtures.map((f) => {
              const { day, month } = formatDayParts(f.date)
              const poisson = f.models.poisson
              const markov = f.models.markov
              return (
                <tr key={f.id} className="border-t border-line hover:bg-cloud-50">
                  <td className="px-2 py-2 whitespace-nowrap text-ink-700">{day} {month}</td>
                  <td className="px-2 py-2 whitespace-nowrap text-ink-900">
                    <span className="inline-flex items-center gap-1.5">
                      <Flag team={f.home_team} size="sm" /> {f.home_team} vs {f.away_team} <Flag team={f.away_team} size="sm" />
                    </span>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-ink-400">{f.venue}</td>
                  <td className="px-2 py-2 text-center font-semibold text-ink-900">
                    {f.actual ? `${f.actual.home}-${f.actual.away}` : '—'}
                  </td>
                  <td className="px-2 py-2 text-center whitespace-nowrap text-ink-700">
                    {poisson.score[0]}-{poisson.score[1]}
                    <span className="text-ink-400"> ({outcomeLabel(poisson.score[0], poisson.score[1])})</span>
                  </td>
                  <td className="px-2 py-2 text-center whitespace-nowrap text-ink-700">
                    {markov.score[0]}-{markov.score[1]}
                    <span className="text-ink-400"> ({outcomeLabel(markov.score[0], markov.score[1])})</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      </div>
    </div>
  )
}
