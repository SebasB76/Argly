import { fmtMoneyK } from '../lib/format'

// Contorno simplificado de Ecuador continental (lng, lat) — fuente: world.geo.json (ECU).
// Se proyecta con la misma transformación que las ciudades, así caen dentro de la silueta.
const OUTLINE = [
  [-80.303, -3.405], [-79.77, -2.658], [-79.987, -2.221], [-80.369, -2.685], [-80.968, -2.247],
  [-80.765, -1.965], [-80.934, -1.057], [-80.583, -0.907], [-80.399, -0.284], [-80.021, 0.36],
  [-80.091, 0.768], [-79.543, 0.983], [-78.855, 1.381], [-77.855, 0.81], [-77.669, 0.826],
  [-77.425, 0.396], [-76.576, 0.257], [-76.292, 0.416], [-75.801, 0.085], [-75.373, -0.152],
  [-75.234, -0.911], [-75.545, -1.562], [-76.635, -2.609], [-77.838, -3.003], [-78.451, -3.873],
  [-78.64, -4.548], [-79.205, -4.959], [-79.625, -4.454], [-80.029, -4.346], [-80.442, -4.426],
  [-80.469, -4.059], [-80.184, -3.821], [-80.303, -3.405],
]

const W = 440
const H = 470
const PAD = 26

// Proyección que conserva la proporción real del país (centrada en el lienzo).
function hacerProyeccion() {
  const lngs = OUTLINE.map((p) => p[0])
  const lats = OUTLINE.map((p) => p[1])
  const lngMin = Math.min(...lngs), lngMax = Math.max(...lngs)
  const latMin = Math.min(...lats), latMax = Math.max(...lats)
  const iw = W - 2 * PAD, ih = H - 2 * PAD
  const s = Math.min(iw / (lngMax - lngMin), ih / (latMax - latMin))
  const offX = PAD + (iw - s * (lngMax - lngMin)) / 2
  const offY = PAD + (ih - s * (latMax - latMin)) / 2
  return {
    x: (lng) => offX + (lng - lngMin) * s,
    y: (lat) => offY + (latMax - lat) * s,
  }
}

const PROJ = hacerProyeccion()
const LAND_PATH = OUTLINE.map((p, i) => `${i ? 'L' : 'M'}${PROJ.x(p[0]).toFixed(1)} ${PROJ.y(p[1]).toFixed(1)}`).join(' ') + ' Z'

export default function MapaCalor({ data }) {
  if (!data) return <div className="cc-loading">Cargando…</div>
  const conCoord = (data.ciudades || []).filter((c) => c.lat != null)
  if (!conCoord.length) return <div className="cc-loading">Sin ciudades georreferenciadas en este dataset.</div>

  const maxA = data.max_alertas || 1
  const radio = (a) => 0.05 * W + Math.sqrt(a / maxA) * 0.13 * W

  return (
    <div className="mapa-wrap">
      <div className="mapa-svg">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Mapa de calor de alertas por ciudad de Ecuador">
          <defs>
            <radialGradient id="heatGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#fde68a" stopOpacity="0.95" />
              <stop offset="32%" stopColor="#fb923c" stopOpacity="0.8" />
              <stop offset="66%" stopColor="#ef4444" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="landGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="#eef2f7" />
            </linearGradient>
            <clipPath id="ecuClip"><path d={LAND_PATH} /></clipPath>
            <filter id="landShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="6" stdDeviation="7" floodColor="#1e293b" floodOpacity="0.16" />
            </filter>
          </defs>

          {/* océano */}
          <rect x="0" y="0" width={W} height={H} className="mapa-ocean" rx="12" />

          {/* tierra */}
          <path d={LAND_PATH} fill="url(#landGrad)" className="mapa-land" filter="url(#landShadow)" />

          {/* capa de calor, recortada a la silueta del país */}
          <g clipPath="url(#ecuClip)" style={{ mixBlendMode: 'multiply' }}>
            {[...conCoord].sort((a, b) => b.alertas - a.alertas).map((c) => (
              <circle key={`heat-${c.ciudad}`} cx={PROJ.x(c.lng)} cy={PROJ.y(c.lat)}
                r={radio(c.alertas)} fill="url(#heatGrad)"
                opacity={0.55 + Math.min(c.tasa_alerta, 0.5)} />
            ))}
          </g>

          {/* borde del país por encima del calor */}
          <path d={LAND_PATH} className="mapa-border" />

          {/* marcadores + etiquetas */}
          {conCoord.map((c, i) => {
            const cx = PROJ.x(c.lng), cy = PROJ.y(c.lat)
            const derecha = cx < W - 92
            const top = c.alertas === maxA
            const tx = derecha ? cx + 10 : cx - 10
            return (
              <g key={`pt-${c.ciudad}`} className={`mapa-pt ${top ? 'top' : ''}`}>
                <title>{`${c.ciudad} · ${c.alertas} alertas (${c.rojos} rojas) · tasa ${(c.tasa_alerta * 100).toFixed(0)}%`}</title>
                {top && <circle cx={cx} cy={cy} r="10" className="mapa-pulse" />}
                <circle cx={cx} cy={cy} r="6.5" className="mapa-ring" />
                <circle cx={cx} cy={cy} r="3" className="mapa-core" />
                <text x={tx} y={cy - 6} textAnchor={derecha ? 'start' : 'end'} className="mapa-city">{c.ciudad}</text>
                <text x={tx} y={cy + 6.5} textAnchor={derecha ? 'start' : 'end'} className="mapa-val">{c.alertas} alertas</text>
              </g>
            )
          })}
        </svg>

        <div className="mapa-legend">
          <div className="lg-scale"><span>menos</span><i /><span>más alertas</span></div>
          <div className="lg-note">tamaño = nº de alertas · intensidad = tasa</div>
        </div>
      </div>

      <div className="mapa-rank">
        <div className="mapa-rank-h">Ranking por alertas</div>
        <ul>
          {data.ciudades.map((c, i) => (
            <li key={c.ciudad} className={i === 0 ? 'top' : ''}>
              <span className="mr-pos">{i + 1}</span>
              <span className="mr-city">{c.ciudad}</span>
              <span className="mr-bar"><i style={{ width: `${(c.alertas / maxA) * 100}%` }} /></span>
              <span className="mr-a">{c.alertas}</span>
              <span className="mr-r" title="alertas rojas">{c.rojos}🔴</span>
              <span className="mr-m">{fmtMoneyK(c.monto_revision)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
