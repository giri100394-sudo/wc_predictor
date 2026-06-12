import { formatDayParts } from '../utils'

export default function DateNav({ dates, counts, selected, onSelect, today }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1">
      {dates.map((date) => {
        const { weekday, day, month } = formatDayParts(date)
        const isSelected = date === selected
        const isToday = date === today
        return (
          <button
            key={date}
            onClick={() => onSelect(date)}
            className={`flex-shrink-0 flex flex-col items-center gap-0.5 rounded-xl px-4 py-2 border transition-all cursor-pointer
              ${isSelected
                ? 'bg-ink-900 text-white border-ink-900 shadow-md scale-[1.03]'
                : 'bg-white border-line text-ink-700 hover:border-ink-400'}
              ${isToday && !isSelected ? 'ring-2 ring-gold-500/60' : ''}`}
          >
            <span className={`text-[10px] uppercase tracking-wide ${isSelected ? 'text-white/60' : 'text-ink-400'}`}>
              {weekday}{isToday ? ' · Today' : ''}
            </span>
            <span className="text-lg font-bold leading-tight">{day} {month}</span>
            <span className={`text-[10px] ${isSelected ? 'text-white/60' : 'text-ink-400'}`}>
              {counts[date]} match{counts[date] !== 1 ? 'es' : ''}
            </span>
          </button>
        )
      })}
    </div>
  )
}
