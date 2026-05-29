const EST = {
  sin_revisar: { txt: 'Sin revisar', cls: 'sr' },
  en_revision: { txt: 'En revisión', cls: 'er' },
  escalado: { txt: 'Escalado', cls: 'es' },
  cerrado: { txt: 'Cerrado', cls: 'ce' },
}

export default function Bandeja({ casos, cargando, onSelect, sel }) {
  const rojos = casos.filter((c) => c.nivel === 'ROJO').length
  const sinRevisar = casos.filter((c) => (c.estado || 'sin_revisar') === 'sin_revisar').length
  return (
    <div className="bandeja">
      <div className="bandeja-h">
        <span className="feed-dot" /> Bandeja
        <span className="count">
          <b>{casos.length}</b> casos · <b className="r">{rojos}</b> rojos · {sinRevisar} sin revisar
        </span>
      </div>
      <div className="bandeja-scroll">
        <table>
          <thead>
            <tr>
              <th>Riesgo</th><th>Siniestro</th><th>Estado</th><th>Motivo principal</th>
              <th>Ramo</th><th>Sucursal</th><th>Monto</th>
            </tr>
          </thead>
          <tbody>
            {cargando && <tr><td colSpan="7" className="muted">▚ Escaneando bandeja…</td></tr>}
            {!cargando && casos.length === 0 && <tr><td colSpan="7" className="muted">Sin señales en este filtro</td></tr>}
            {!cargando && casos.map((c) => {
              const e = EST[c.estado] || EST.sin_revisar
              return (
                <tr key={c.id_siniestro} className={sel === c.id_siniestro ? 'sel' : ''} onClick={() => onSelect(c.id_siniestro)}>
                  <td>
                    <div className={`risk-cell ${c.nivel.toLowerCase()}`}>
                      <span className="badge">{c.score}</span>
                      <span className="riskbar"><i style={{ width: `${Math.min(100, c.score)}%` }} /></span>
                    </div>
                  </td>
                  <td className="mono">{c.id_siniestro}</td>
                  <td><span className={`est-badge ${e.cls}`}>{e.txt}</span></td>
                  <td>{c.motivo_principal}</td>
                  <td>{c.ramo}</td>
                  <td>{c.sucursal}</td>
                  <td className="mono">${c.monto_reclamado.toLocaleString('es-EC', { maximumFractionDigits: 0 })}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
