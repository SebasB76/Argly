export default function Bandeja({ casos, cargando, onSelect, sel }) {
  return (
    <div className="bandeja">
      <div className="bandeja-h">Most Wanted · {casos.length} casos</div>
      <table>
        <thead>
          <tr>
            <th>Riesgo</th><th>Siniestro</th><th>Motivo principal</th>
            <th>Ramo</th><th>Sucursal</th><th>Monto</th>
          </tr>
        </thead>
        <tbody>
          {cargando && <tr><td colSpan="6" className="muted">Cargando…</td></tr>}
          {!cargando && casos.length === 0 && <tr><td colSpan="6" className="muted">Sin casos</td></tr>}
          {!cargando && casos.map((c) => (
            <tr key={c.id_siniestro} className={sel === c.id_siniestro ? 'sel' : ''} onClick={() => onSelect(c.id_siniestro)}>
              <td><span className={`badge ${c.nivel.toLowerCase()}`}>{c.score}</span></td>
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
  )
}
