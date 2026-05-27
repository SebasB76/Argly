import { useEffect, useState } from 'react'
import { getRedes } from '../api'

export default function Redes() {
  const [redes, setRedes] = useState([])

  useEffect(() => { getRedes().then((d) => setRedes(d.redes || [])).catch(() => {}) }, [])

  if (!redes.length) return null
  return (
    <div className="redes">
      <div className="redes-h">🕸️ Redes detectadas · {redes.length} (proveedores que concentran siniestros)</div>
      <div className="redes-list">
        {redes.slice(0, 6).map((r, i) => (
          <div key={i} className="red-card">
            <div className="red-prov">{r.proveedores.join(', ')}</div>
            <div className="red-stats">{r.n_siniestros} siniestros · {r.n_asegurados} asegurados</div>
            <div className="red-monto">${r.monto_total.toLocaleString('es-EC', { maximumFractionDigits: 0 })}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
