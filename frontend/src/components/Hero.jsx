export default function Hero() {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-gold-500/30 bg-gradient-to-br from-pitch-700 via-pitch-800 to-navy-800 p-6 sm:p-8 mb-6 shadow-2xl">
      <div className="pointer-events-none absolute -top-24 -right-24 w-72 h-72 bg-mint-500/20 rounded-full blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 w-72 h-72 bg-sky-500/20 rounded-full blur-3xl" />
      <div className="relative flex items-center gap-4 flex-wrap">
        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-white/5 border border-gold-500/40 text-3xl animate-pulse-glow shrink-0">
          ⚽
        </div>
        <div>
          <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-white">
            World Cup 2026 Prediction Agent
          </h1>
          <p className="text-gold-400 font-semibold mt-1">
            Group Stage — 11 to 27 June · Canada · Mexico · USA
          </p>
          <p className="text-white/50 text-sm mt-1 max-w-2xl">
            Poisson and Markov-chain models, optimized for your league:
            5 exact · 3 result · −2 wrong winner (draws penalty-free) · +2 scorer
          </p>
        </div>
      </div>
    </div>
  )
}
