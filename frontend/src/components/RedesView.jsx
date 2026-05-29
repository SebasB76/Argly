import { useEffect, useState } from 'react'
import { getRedes } from '../api'
import { fmtMoney, fmtMoneyK, fmtNum } from '../lib/format'
import CasoModal from './CasoModal'

// Mini-grafo: proveedor (hub) al centro, asegurados conectados alrededor.
function HubGraph({ nAseg }) {
  const N = Math.min(nAseg, 12)
  const cx = 90, cy = 70, R = 50
  const nodos = Array.from({ length: N }, (_, i) => {
    const ang = (i / N) * 2 * Math.PI - Math.PI / 2
    return { x: cx + R * Math.cos(ang), y: cy + R * Math.sin(ang) }
  })
  return (
    <svg className="hubsvg" viewBox="0 0 180 140" role="img" aria-label="Grafo del anillo">
      {nodos.map((n, i) => <line key={`l${i}`} x1={cx} y1={cy} x2={n.x} y2={n.y} className="hub-edge" />)}
      {nodos.map((n, i) => <circle key={`a${i}`} cx={n.x} cy={n.y} r="5" className="hub-aseg" />)}
      <circle cx={cx} cy={cy} r="12" className="hub-prov" />
      <text x={cx} y={cy + 3.5} textAnchor="middle" className="hub-prov-tx">P</text>
      {nAseg > N && <text x={cx} y={132} textAnchor="middle" className="hub-mas">+{nAseg - N} asegurados más</text>}
    </svg>
  )
}

function ratioTexto(r) {
  if (r >= 3) return { txt: 'concentración muy alta', cls: 'alto' }
  if (r >= 2) return { txt: 'concentración alta', cls: 'alto' }
  if (r >= 1.5) return { txt: 'concentración a vigilar', cls: 'medio' }
  return { txt: 'concentración moderada', cls: 'bajo' }
}

export default function RedesView() {
  const [redes, setRedes] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [casoId, setCasoId] = useState(null)

  useEffect(() => {
    getRedes().then((d) => setRedes(d.redes || [])).catch(() => {}).finally(() => setLoaded(true))
  }, [])

  const maxS = Math.max(...redes.map((r) => r.n_siniestros), 1)
  const totSin = redes.reduce((s, r) => s + r.n_siniestros, 0)
  const totAseg = redes.reduce((s, r) => s + r.n_asegurados, 0)
  const totMonto = redes.reduce((s, r) => s + r.monto_total, 0)

  return (
    <div className="redes-view">
      <div className="sec-head">
        <span className="sec-eyebrow">Grafo de relaciones</span>
        <h2 className="sec-title">Redes de fraude</h2>
        <span className="redes-count">{redes.length} anillos</span>
      </div>

      {/* Contexto: qué es y cómo leerlo */}
      <div className="redes-explica">
        <p>
          Un <b>anillo</b> es un <b>proveedor</b> (taller, clínica, perito…) que concentra siniestros
          sospechosos de <b>varios asegurados distintos</b>. Lo detectamos con un grafo que conecta cada
          proveedor con los asegurados de sus reclamos no-verdes.
        </p>
        <ul>
          <li><span className="re-dot prov" /> El nodo central es el <b>proveedor</b>; alrededor, los <b>asegurados</b> conectados.</li>
          <li>Muchos siniestros con <b>pocos asegurados</b> (ratio alto) es la firma típica de fraude organizado.</li>
          <li>Es una <b>alerta para investigar</b>, no una acusación. La decisión es del analista.</li>
        </ul>
      </div>

      {/* Resumen */}
      {redes.length > 0 && (
        <div className="redes-kpis">
          <div className="rk"><b>{fmtNum(redes.length)}</b><span>Anillos detectados</span></div>
          <div className="rk"><b>{fmtNum(totSin)}</b><span>Siniestros en redes</span></div>
          <div className="rk"><b>{fmtNum(totAseg)}</b><span>Asegurados vinculados</span></div>
          <div className="rk alerta"><b>{fmtMoneyK(totMonto)}</b><span>Exposición total</span></div>
        </div>
      )}

      {loaded && redes.length === 0 && <div className="muted">Sin redes detectadas en la bandeja actual.</div>}

      <div className="redes-grid">
        {redes.map((r, i) => {
          const ratio = r.n_asegurados ? r.n_siniestros / r.n_asegurados : r.n_siniestros
          const info = ratioTexto(ratio)
          return (
            <div className="ringcard" key={i} style={{ animationDelay: `${i * 50}ms` }}>
              <div className="ring-top">
                <span className="ring-tag">RING-{String(i + 1).padStart(2, '0')}</span>
                <span className="ring-monto">{fmtMoney(r.monto_total)}</span>
              </div>

              <HubGraph nAseg={r.n_asegurados} />

              <div className="ring-prov-row">Proveedor <b className="mono">{r.proveedores.join(', ')}</b></div>

              <div className={`ring-ratio ${info.cls}`}>
                <b>{ratio.toFixed(1)}</b> siniestros por asegurado
                <span className="ring-ratio-hint">{info.txt}</span>
              </div>

              <div className="ring-bar"><i style={{ width: `${(r.n_siniestros / maxS) * 100}%` }} /></div>
              <div className="ring-stats">
                <span><b>{r.n_siniestros}</b> siniestros</span>
                <span><b>{r.n_asegurados}</b> asegurados</span>
              </div>

              {r.siniestros?.length > 0 && (
                <details className="ring-casos">
                  <summary>Ver {r.siniestros.length} siniestros del anillo</summary>
                  <div className="ring-casos-list">
                    {r.siniestros.map((id) => (
                      <button key={id} className="mono" onClick={() => setCasoId(id)}>{id}</button>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )
        })}
      </div>

      <CasoModal id={casoId} onClose={() => setCasoId(null)} />
    </div>
  )
}
