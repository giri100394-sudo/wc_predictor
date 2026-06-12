export default function Hero() {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-line bg-white p-6 sm:p-8 mb-6 shadow-sm">
      <div className="pointer-events-none absolute -top-24 -right-24 w-72 h-72 bg-mint-50 rounded-full blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 w-72 h-72 bg-sky-50 rounded-full blur-3xl" />

      <div className="relative">
        <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-ink-900">
          World Cup 2026 Prediction Agent
        </h1>
        <p className="text-gold-600 font-semibold mt-1">
          Group Stage — 11 to 27 June · Canada · Mexico · USA
        </p>
      </div>

      <p className="relative text-ink-400 text-sm mt-3 max-w-2xl">
        Poisson and Markov-chain models, optimized for your league:
        5 exact · 3 result · −2 wrong winner (draws penalty-free) · +2 scorer
      </p>
    </div>
  )
}
