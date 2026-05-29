import { ParetoChart } from '../charts'
import { fmtMoney } from '../../lib/format'

export default function RedCard({ herramienta, datos }) {
  if (herramienta === 'proveedores_pareto') {
    const items = (datos?.proveedores || []).map((p) => ({ label: p.id_proveedor, value: p.alertas, cum: p.pct_acumulado }))
    return (
      <div className="chatwidget">
        <div className="cw-head">Pareto · proveedores con alertas rojas</div>
        {items.length ? <ParetoChart items={items} target={datos.objetivo_pct || 80} /> : <div className="cw-cap">Sin datos.</div>}
        {datos?.interpretacion && <div className="cw-cap">{datos.interpretacion}</div>}
      </div>
    )
  }

  if (herramienta === 'redes') {
    const rings = Array.isArray(datos) ? datos : (datos?.redes || [])
    return (
      <div className="chatwidget">
        <div className="cw-head">Anillos detectados · {rings.length}</div>
        <div className="cw-rings">
          {rings.slice(0, 6).map((r, i) => (
            <div className="cw-ring" key={i}>
              <span className="mono cw-ring-prov">{(r.proveedores || []).join(' · ')}</span>
              <span className="cw-ring-stat">{r.n_siniestros} sin · {r.n_asegurados} aseg · <b>{fmtMoney(r.monto_total)}</b></span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // proveedores_top: barras simples
  const list = Array.isArray(datos) ? datos : []
  const max = Math.max(...list.map((x) => x.alertas || 0), 1)
  return (
    <div className="chatwidget">
      <div className="cw-head">Proveedores con más alertas</div>
      <ul className="cw-bars">
        {list.slice(0, 8).map((x, i) => (
          <li key={i}>
            <span className="mono cw-bar-l">{x.id_proveedor}</span>
            <span className="cw-bar"><i style={{ width: `${(x.alertas / max) * 100}%` }} /></span>
            <span className="cw-bar-v">{x.alertas}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
