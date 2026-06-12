import { useState } from 'react'
import { flag, flagUrl } from '../flags'

const SIZES = {
  sm: 'w-5 h-5 text-xs',
  md: 'w-7 h-7 text-sm',
  lg: 'w-11 h-11 text-2xl',
}

export default function Flag({ team, size = 'md', className = '' }) {
  const [errored, setErrored] = useState(false)
  const url = flagUrl(team)
  const wrap = `inline-flex items-center justify-center rounded-full overflow-hidden ring-1 ring-black/5 bg-cloud-100 shrink-0 ${SIZES[size]} ${className}`

  if (!url || errored) {
    return <span className={wrap}>{flag(team)}</span>
  }

  return (
    <span className={wrap}>
      <img
        src={url}
        alt=""
        className="w-full h-full object-cover"
        onError={() => setErrored(true)}
      />
    </span>
  )
}
