import { useState } from 'react'
import { refreshScorers } from '../api'

export default function ScorerRefresh({ date, matchCount, onDone }) {
  const [stage, setStage] = useState('idle') // idle | confirm | loading | done | error
  const [result, setResult] = useState(null)

  if (!matchCount) return null

  async function handleConfirm() {
    setStage('loading')
    try {
      const data = await refreshScorers(date)
      setResult(data)
      setStage('done')
      onDone?.()
    } catch (err) {
      setResult({ error: err.message })
      setStage('error')
    }
  }

  return (
    <div className="mb-4">
      {stage === 'idle' && (
        <button
          onClick={() => setStage('confirm')}
          className="text-xs font-semibold text-sky-600 hover:text-sky-500 cursor-pointer"
        >
          ⟳ Refresh scorer predictions for this day
        </button>
      )}

      {stage === 'confirm' && (
        <div className="rounded-xl border border-gold-500/40 bg-gold-50 p-3 text-sm text-ink-900">
          <p className="mb-2">
            Refresh AI scorer predictions for {matchCount} match{matchCount !== 1 ? 'es' : ''} on this
            day? This calls Claude with web search for each match — real API cost, and can take
            10-30 seconds per match.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirm}
              className="rounded-full bg-gold-500 text-ink-900 font-semibold px-3 py-1 text-xs cursor-pointer hover:bg-gold-600"
            >
              Yes, refresh
            </button>
            <button
              onClick={() => setStage('idle')}
              className="rounded-full bg-cloud-100 text-ink-700 px-3 py-1 text-xs cursor-pointer hover:bg-cloud-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {stage === 'loading' && (
        <div className="text-xs text-ink-400">
          Refreshing scorer predictions for {matchCount} match{matchCount !== 1 ? 'es' : ''}… this can
          take a minute or two.
        </div>
      )}

      {stage === 'done' && (
        <div className="text-xs text-mint-600">
          Done — updated {result.updated} of {result.total} match{result.total !== 1 ? 'es' : ''}.
          <button onClick={() => setStage('idle')} className="ml-2 text-ink-400 underline cursor-pointer">
            dismiss
          </button>
        </div>
      )}

      {stage === 'error' && (
        <div className="text-xs text-coral-500">
          Refresh failed: {result.error}
          <button onClick={() => setStage('idle')} className="ml-2 text-ink-400 underline cursor-pointer">
            dismiss
          </button>
        </div>
      )}
    </div>
  )
}
