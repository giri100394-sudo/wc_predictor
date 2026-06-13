import Flag from './Flag'
import { formatDayParts } from '../utils'

const RESULT_STYLES = {
  W: 'bg-mint-500 text-white',
  D: 'bg-cloud-100 text-ink-700',
  L: 'bg-coral-500 text-white',
}

export default function TeamForm({ team, form }) {
  return (
    <div className="flex-1 min-w-[260px]">
      <div className="flex items-center gap-2 mb-1.5">
        <Flag team={team} size="sm" />
        <span className="text-sm font-semibold text-ink-900">{team}</span>
      </div>
      {form && form.length > 0 ? (
        <div className="flex flex-col">
          {form.map((e, i) => {
            const { day, month } = formatDayParts(e.date)
            return (
              <div
                key={i}
                className="flex items-center gap-2 text-xs py-1.5 border-b border-line last:border-0"
              >
                <span
                  className={`w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold shrink-0 ${RESULT_STYLES[e.result]}`}
                >
                  {e.result}
                </span>
                <span className="font-semibold text-ink-900 shrink-0">
                  {e.score_for}-{e.score_against}
                </span>
                <span className="text-ink-700 truncate">vs {e.opponent}</span>
                <span className="text-ink-400 text-[10px] ml-auto shrink-0 whitespace-nowrap">
                  {e.tournament}
                </span>
                <span className="text-ink-400 text-[10px] shrink-0 whitespace-nowrap">
                  {day} {month}
                </span>
              </div>
            )
          })}
        </div>
      ) : (
        <span className="text-[11px] text-ink-400">No recent results</span>
      )}
    </div>
  )
}
