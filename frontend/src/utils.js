export function outcomeLabel(a, b) {
  if (a > b) return '1'
  if (a < b) return '2'
  return 'X'
}

export function todayStr() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function pickDefaultDate(dates, today) {
  if (dates.includes(today)) return today
  const future = dates.filter((d) => d >= today)
  if (future.length) return future[0]
  return dates[dates.length - 1]
}

export function formatDayParts(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`)
  return {
    weekday: d.toLocaleDateString('en-US', { weekday: 'short' }),
    day: d.getDate(),
    month: d.toLocaleDateString('en-US', { month: 'short' }),
  }
}

export function formatFullDate(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`)
  return d.toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

export const HIT_LABELS = {
  exact: 'Exact',
  result: 'Result',
  wrong_winner: 'Wrong winner',
  wrong: 'Wrong',
}

export const HIT_STYLES = {
  exact: 'bg-mint-500 text-pitch-900',
  result: 'bg-gold-500 text-pitch-900',
  wrong_winner: 'bg-coral-500 text-white',
  wrong: 'bg-white/15 text-white/70',
}
