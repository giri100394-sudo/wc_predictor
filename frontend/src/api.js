const BASE = import.meta.env.VITE_API_BASE ?? ''

export async function fetchFixtures() {
  const res = await fetch(`${BASE}/api/fixtures`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}
