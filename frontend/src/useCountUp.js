import { useEffect, useRef, useState } from 'react'

// Animates a number from 0 → target with an easeOutCubic ramp.
// Non-numeric targets are returned verbatim (no animation).
export function useCountUp(target, { duration = 1100 } = {}) {
  const [val, setVal] = useState(0)
  const raf = useRef(0)

  useEffect(() => {
    if (typeof target !== 'number' || Number.isNaN(target)) {
      setVal(target)
      return undefined
    }
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce) { setVal(target); return undefined }

    let start = null
    const step = (now) => {
      if (start === null) start = now
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3)
      setVal(target * eased)
      if (t < 1) raf.current = requestAnimationFrame(step)
    }
    raf.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf.current)
  }, [target, duration])

  return typeof target === 'number' ? Math.round(val) : val
}
