export default function ProbBar({ home, draw, away }) {
  return (
    <div className="flex h-2.5 rounded-full overflow-hidden ring-1 ring-black/5">
      <div className="bg-mint-500 transition-all" style={{ width: `${home * 100}%` }} />
      <div className="bg-gold-500 transition-all" style={{ width: `${draw * 100}%` }} />
      <div className="bg-sky-500 transition-all" style={{ width: `${away * 100}%` }} />
    </div>
  )
}
