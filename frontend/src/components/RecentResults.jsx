import Flag from './Flag'
import { formatDayParts } from '../utils'

export default function RecentResults({ fixtures }) {
  const recent = fixtures
    .filter((f) => f.actual !== null)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 5)

  if (recent.length === 0) return null

  return (
    <div className="mb-5">
      <h3 className="text-xs font-semibold text-ink-400 uppercase tracking-wide mb-2">
        Recent results
      </h3>
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {recent.map((f) => {
          const { day, month } = formatDayParts(f.date)
          return (
            <div
              key={f.id}
              className="flex-shrink-0 flex items-center gap-2 rounded-xl border border-line bg-white px-3 py-2 shadow-sm"
            >
              <Flag team={f.home_team} size="sm" />
              <span className="font-bold text-ink-900 text-sm">
                {f.actual.home} – {f.actual.away}
              </span>
              <Flag team={f.away_team} size="sm" />
              <span className="text-[10px] text-ink-400 ml-1 whitespace-nowrap">{day} {month}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
