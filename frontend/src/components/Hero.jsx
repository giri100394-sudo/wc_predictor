import stadiumImg from '../assets/stadium-night.avif'
import emblemImg from '../assets/wc-emblem.webp'

export default function Hero() {
  return (
    <div className="relative overflow-hidden rounded-3xl mb-6 shadow-sm">
      <img
        src={stadiumImg}
        alt=""
        className="absolute inset-0 w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-ink-900/90 via-ink-900/75 to-ink-900/40" />

      <div className="relative p-6 sm:p-8 flex items-center justify-between gap-6">
        <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-white">
          World Cup 2026 Prediction Agent
        </h1>
        <img
          src={emblemImg}
          alt="FIFA World Cup 26"
          className="hidden sm:block w-20 h-20 object-contain drop-shadow-lg shrink-0"
        />
      </div>
    </div>
  )
}
