import { fmtPct } from '../lib/format'

/* ---- shared chart panel frame ---- */
export function ChartCard({ eyebrow, title, sub, right, children, span }) {
  return (
    <div className={`chartcard ${span || ''}`}>
      <div className="cc-head">
        <div>
          {eyebrow && <div className="cc-eyebrow">{eyebrow}</div>}
          <h3 className="cc-title">{title}</h3>
        </div>
        {right && <div className="cc-right">{right}</div>}
      </div>
      {sub && <div className="cc-sub">{sub}</div>}
      <div className="cc-body">{children}</div>
    </div>
  )
}

/* ---- donut (distribution) ---- */
export function Donut({ segments, centerValue, centerLabel }) {
  const sum = segments.reduce((a, s) => a + s.value, 0) || 1
  let acc = 0
  const R = 15.9155
  return (
    <div className="donut">
      <svg viewBox="0 0 36 36" className="donut-svg" role="img" aria-label="Distribución">
        <circle className="donut-track" cx="18" cy="18" r={R} />
        <g className="donut-rot">
          {segments.map((s, i) => {
            const pct = (s.value / sum) * 100
            const seg = (
              <circle
                key={i}
                className="donut-seg"
                cx="18" cy="18" r={R}
                stroke={s.color}
                strokeDasharray={`${pct} ${100 - pct}`}
                strokeDashoffset={-acc}
                style={{ animationDelay: `${i * 110}ms` }}
              />
            )
            acc += pct
            return seg
          })}
        </g>
      </svg>
      <div className="donut-center">
        <b>{centerValue}</b>
        <span>{centerLabel}</span>
      </div>
      <ul className="donut-legend">
        {segments.map((s, i) => (
          <li key={i}>
            <i style={{ background: s.color }} />
            <span className="dl-label">{s.label}</span>
            <span className="dl-val">{s.value.toLocaleString('es-EC')}</span>
            <span className="dl-pct">{fmtPct((s.value / sum) * 100, 1)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ---- pareto (bars + cumulative % + target line) ---- */
export function ParetoChart({ items, target = 80, maxBars = 16 }) {
  const data = items.slice(0, maxBars)
  const W = 340, H = 150, padL = 6, padR = 6, padT = 12, padB = 22
  const plotW = W - padL - padR, plotH = H - padT - padB
  const maxVal = Math.max(...data.map((d) => d.value), 1)
  const bw = plotW / data.length
  const x = (i) => padL + i * bw + bw / 2
  const yBar = (v) => padT + plotH - (v / maxVal) * plotH
  const yCum = (p) => padT + plotH - (p / 100) * plotH
  const linePts = data.map((d, i) => `${x(i)},${yCum(d.cum)}`).join(' ')
  return (
    <div className="pareto">
      <svg viewBox={`0 0 ${W} ${H}`} className="pareto-svg" preserveAspectRatio="none">
        {/* gridlines for cumulative % */}
        {[0, 50, 100].map((p) => (
          <line key={p} className="grid-line" x1={padL} x2={W - padR} y1={yCum(p)} y2={yCum(p)} />
        ))}
        {/* target reference */}
        <line className="target-line" x1={padL} x2={W - padR} y1={yCum(target)} y2={yCum(target)} />
        <text className="target-label" x={W - padR - 2} y={yCum(target) - 3} textAnchor="end">{target}% acumulado</text>
        {/* bars */}
        {data.map((d, i) => {
          const h = (d.value / maxVal) * plotH
          return (
            <rect
              key={i}
              className={`pareto-bar ${d.cum <= target ? 'in' : 'out'}`}
              x={padL + i * bw + bw * 0.16}
              y={padT + plotH - h}
              width={bw * 0.68}
              height={Math.max(h, 1)}
              style={{ animationDelay: `${i * 35}ms` }}
            />
          )
        })}
        {/* cumulative line + dots */}
        <polyline className="cum-line" points={linePts} />
        {data.map((d, i) => (
          <circle key={i} className="cum-dot" cx={x(i)} cy={yCum(d.cum)} r="2" style={{ animationDelay: `${300 + i * 35}ms` }} />
        ))}
      </svg>
      <div className="pareto-x">
        {data.map((d, i) => (
          <span key={i} className="px-tick" style={{ width: `${100 / data.length}%` }}>{d.label.replace(/^P0*/, 'P')}</span>
        ))}
      </div>
    </div>
  )
}

/* ---- horizontal bars (SHAP importances) ---- */
export function BarsH({ items, max = 10, accent = 'var(--phos)' }) {
  const data = items.slice(0, max)
  const maxVal = Math.max(...data.map((d) => d.value), 0.0001)
  return (
    <ul className="barsh">
      {data.map((d, i) => (
        <li key={i} style={{ animationDelay: `${i * 45}ms` }}>
          <span className="bh-label" title={d.label}>{d.label}</span>
          <span className="bh-track">
            <i style={{ width: `${(d.value / maxVal) * 100}%`, background: accent }} />
          </span>
          <span className="bh-val">{(d.value * 100).toFixed(1)}</span>
        </li>
      ))}
    </ul>
  )
}

/* ---- segmented bar (savings breakdown) ---- */
export function Segmented({ segments, total, totalLabel }) {
  const sum = segments.reduce((a, s) => a + s.value, 0) || 1
  return (
    <div className="segmented">
      <div className="seg-total"><b>{total}</b><span>{totalLabel}</span></div>
      <div className="seg-bar">
        {segments.map((s, i) => (
          <i key={i} style={{ width: `${(s.value / sum) * 100}%`, background: s.color, animationDelay: `${i * 120}ms` }} title={s.label} />
        ))}
      </div>
      <ul className="seg-legend">
        {segments.map((s, i) => (
          <li key={i}>
            <i style={{ background: s.color }} />
            <span className="sl-label">{s.label}</span>
            <span className="sl-val">{s.display}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ---- histogram (score distribution) ---- */
export function Histogram({ scores, bins = 10 }) {
  const counts = new Array(bins).fill(0)
  scores.forEach((s) => {
    const idx = Math.min(bins - 1, Math.floor((s / 100) * bins))
    counts[idx] += 1
  })
  const maxC = Math.max(...counts, 1)
  const bandColor = (i) => {
    const mid = (i + 0.5) * (100 / bins)
    if (mid >= 70) return 'var(--rojo)'
    if (mid >= 40) return 'var(--amar)'
    return 'var(--verde)'
  }
  return (
    <div className="histogram">
      <div className="hist-bars">
        {counts.map((c, i) => (
          <div className="hist-col" key={i} title={`${i * (100 / bins)}–${(i + 1) * (100 / bins)}: ${c}`}>
            <span className="hc-count">{c || ''}</span>
            <i style={{ height: `${(c / maxC) * 100}%`, background: bandColor(i), animationDelay: `${i * 50}ms` }} />
          </div>
        ))}
      </div>
      <div className="hist-axis"><span>0</span><span>score</span><span>100</span></div>
    </div>
  )
}
