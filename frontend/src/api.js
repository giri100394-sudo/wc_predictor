const BASE = import.meta.env.VITE_API_BASE ?? ''

export async function fetchFixtures() {
  const res = await fetch(`${BASE}/api/fixtures`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export async function refreshScorers(date) {
  const res = await fetch(`${BASE}/api/refresh-scorers/${date}`, { method: 'POST' })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}
