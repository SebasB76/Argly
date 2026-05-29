export default function Bandeja({ casos, cargando, onSelect, sel }) {
  return (
    <div className="bandeja">
      <div className="bandeja-h">
        <span className="feed-dot" /> Feed en vivo
        <span className="count">{casos.length} señales</span>
      </div>
      <div className="bandeja-scroll">
        <table>
          <thead>
            <tr>
              <th>Riesgo</th><th>Siniestro</th><th>Motivo principal</th>
              <th>Ramo</th><th>Sucursal</th><th>Monto</th>
            </tr>
          </thead>
          <tbody>
            {cargando && <tr><td colSpan="6" className="muted">▚ Escaneando bandeja…</td></tr>}
            {!cargando && casos.length === 0 && <tr><td colSpan="6" className="muted">Sin señales en este filtro</td></tr>}
            {!cargando && casos.map((c) => (
              <tr key={c.id_siniestro} className={sel === c.id_siniestro ? 'sel' : ''} onClick={() => onSelect(c.id_siniestro)}>
                <td>
                  <div className={`risk-cell ${c.nivel.toLowerCase()}`}>
                    <span className="badge">{c.score}</span>
                    <span className="riskbar"><i style={{ width: `${Math.min(100, c.score)}%` }} /></span>
                  </div>
                </td>
                <td className="mono">{c.id_siniestro}</td>
                <td>{c.motivo_principal}</td>
                <td>{c.ramo}</td>
                <td>{c.sucursal}</td>
                <td className="mono">${c.monto_reclamado.toLocaleString('es-EC', { maximumFractionDigits: 0 })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
