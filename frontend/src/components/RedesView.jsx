import { useEffect, useState } from 'react'
import { getRedes } from '../api'
import { fmtMoney } from '../lib/format'

export default function RedesView() {
  const [redes, setRedes] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    getRedes().then((d) => setRedes(d.redes || [])).catch(() => {}).finally(() => setLoaded(true))
  }, [])

  const maxS = Math.max(...redes.map((r) => r.n_siniestros), 1)

  return (
    <div className="redes-view">
      <div className="sec-head">
        <span className="sec-eyebrow">Grafo de relaciones</span>
        <h2 className="sec-title">Redes detectadas</h2>
        <span className="redes-count">{redes.length} anillos</span>
      </div>
      <p className="redes-intro">
        Proveedores que concentran siniestros de múltiples asegurados — candidatos a fraude organizado.
        Es una señal para revisión, <b>no una acusación</b>.
      </p>

      {loaded && redes.length === 0 && <div className="muted">Sin redes detectadas</div>}

      <div className="redes-grid">
        {redes.map((r, i) => (
          <div className="ringcard" key={i} style={{ animationDelay: `${i * 50}ms` }}>
            <div className="ring-top">
              <span className="ring-tag">RING-{String(i + 1).padStart(2, '0')}</span>
              <span className="ring-monto">{fmtMoney(r.monto_total)}</span>
            </div>
            <div className="ring-prov">{r.proveedores.join(' · ')}</div>
            <div className="ring-bar"><i style={{ width: `${(r.n_siniestros / maxS) * 100}%` }} /></div>
            <div className="ring-stats">
              <span><b>{r.n_siniestros}</b> siniestros</span>
              <span><b>{r.n_asegurados}</b> asegurados</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
