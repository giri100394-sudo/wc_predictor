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
                ? 'bg-gold-500 text-pitch-900 border-gold-500 shadow-lg shadow-gold-500/30 scale-[1.03]'
                : 'bg-white/5 border-white/10 text-white/80 hover:bg-white/10'}
              ${isToday && !isSelected ? 'ring-2 ring-gold-400/70' : ''}`}
          >
            <span className="text-[10px] uppercase tracking-wide opacity-70">
              {weekday}{isToday ? ' · Today' : ''}
            </span>
            <span className="text-lg font-bold leading-tight">{day} {month}</span>
            <span className="text-[10px] opacity-70">
              {counts[date]} match{counts[date] !== 1 ? 'es' : ''}
            </span>
          </button>
        )
      })}
    </div>
  )
}
