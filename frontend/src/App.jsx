import { useEffect, useMemo, useState } from 'react'
import { fetchFixtures } from './api'
import { todayStr, pickDefaultDate, formatFullDate } from './utils'
import Hero from './components/Hero'
import Tabs from './components/Tabs'
import DateNav from './components/DateNav'
import MatchCard from './components/MatchCard'
import RecentResults from './components/RecentResults'
import FixturesOverview from './components/FixturesOverview'
import GroupStage from './components/GroupStage'

export default function App() {
  const [fixtures, setFixtures] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('matchday')
  const [selectedDate, setSelectedDate] = useState(null)

  useEffect(() => {
    fetchFixtures()
      .then((data) => {
        setFixtures(data)
        const dates = [...new Set(data.map((f) => f.date))].sort()
        setSelectedDate(pickDefaultDate(dates, todayStr()))
      })
      .catch((err) => setError(err.message))
  }, [])

  const { dates, counts } = useMemo(() => {
    if (!fixtures) return { dates: [], counts: {} }
    const dates = [...new Set(fixtures.map((f) => f.date))].sort()
    const counts = {}
    for (const f of fixtures) counts[f.date] = (counts[f.date] || 0) + 1
    return { dates, counts }
  }, [fixtures])

  const dayMatches = useMemo(() => {
    if (!fixtures || !selectedDate) return []
    return fixtures.filter((f) => f.date === selectedDate)
  }, [fixtures, selectedDate])

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 sm:py-8">
      <Hero />

      {error && (
        <div className="rounded-xl border border-coral-500/40 bg-coral-500/10 text-coral-500 p-4 mb-6">
          Failed to load fixtures: {error}. Is the API running on port 8000?
        </div>
      )}

      {!fixtures && !error && (
        <div className="text-center text-ink-400 py-20">Loading fixtures…</div>
      )}

      {fixtures && (
        <>
          <Tabs active={activeTab} onChange={setActiveTab} />

          {activeTab === 'matchday' && (
            <div>
              <RecentResults fixtures={fixtures} />

              <DateNav
                dates={dates}
                counts={counts}
                selected={selectedDate}
                onSelect={setSelectedDate}
                today={todayStr()}
              />

              {selectedDate && (
                <p className="text-ink-400 text-sm mt-3 mb-4">
                  {formatFullDate(selectedDate)} · {dayMatches.length} match
                  {dayMatches.length !== 1 ? 'es' : ''}
                </p>
              )}

              <div className="flex flex-col gap-4">
                {dayMatches.map((f, i) => (
                  <MatchCard key={f.id} fixture={f} index={i} />
                ))}
              </div>
            </div>
          )}

          {activeTab === 'fixtures' && <FixturesOverview fixtures={fixtures} />}

          {activeTab === 'group' && <GroupStage fixtures={fixtures} />}
        </>
      )}
    </div>
  )
}
