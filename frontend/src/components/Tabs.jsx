const TABS = [
  { id: 'matchday', label: 'Matchday' },
  { id: 'fixtures', label: 'All fixtures' },
  { id: 'group', label: 'Group stage so far' },
]

export default function Tabs({ active, onChange }) {
  return (
    <div className="flex gap-2 mb-6 bg-white/5 border border-white/10 rounded-full p-1 w-fit">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors cursor-pointer
            ${active === t.id
              ? 'bg-gold-500 text-pitch-900 shadow-md shadow-gold-500/30'
              : 'text-white/60 hover:text-white hover:bg-white/5'}`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
