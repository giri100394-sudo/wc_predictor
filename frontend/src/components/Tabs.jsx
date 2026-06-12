const TABS = [
  { id: 'matchday', label: 'Matchday' },
  { id: 'fixtures', label: 'All fixtures' },
  { id: 'group', label: 'Model performance' },
]

export default function Tabs({ active, onChange }) {
  return (
    <div className="flex gap-1 mb-6 bg-cloud-100 rounded-full p-1 w-fit">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors cursor-pointer
            ${active === t.id
              ? 'bg-white text-ink-900 shadow-sm'
              : 'text-ink-400 hover:text-ink-900'}`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
