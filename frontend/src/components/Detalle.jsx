export default function Detalle({ d, onClose }) {
  if (!d) return <div className="detalle vacio">Selecciona una señal de la bandeja para abrir su dossier.</div>

  const nivel = d.nivel.toLowerCase()
  const contribs = [...(d.contribuciones || [])].sort((a, b) => b.puntos - a.puntos)
  return (
    <div className="detalle">
      <div className="detalle-h">
        <div className={`scoregauge ${nivel}`}>
          <span className="sg-num">{d.score}</span>
          <span className="sg-cap">SCORE</span>
        </div>
        <div>
          <div className="mono big">{d.id_siniestro}</div>
          <div className={`nivel ${nivel}`}>{d.nivel}</div>
        </div>
        <button className="x" onClick={onClose} aria-label="Cerrar">×</button>
      </div>

      <div className="reco">{d.recomendacion}</div>
      <div className="meta">
        {d.ramo} · {d.cobertura} · {d.sucursal} · ${d.monto_reclamado.toLocaleString('es-EC', { maximumFractionDigits: 0 })}
      </div>
      <a className="pdf-btn" href={`/api/casos/${d.id_siniestro}/dossier`} target="_blank" rel="noreferrer">↓ Descargar dossier PDF</a>

      <div className="contrib-h">Por qué · {contribs.length} señales</div>
      <ul className="contribs">
        {contribs.map((c, i) => (
          <li key={i} className={c.gate ? 'gate' : ''} style={{ animationDelay: `${i * 45}ms` }}>
            <span className="pts">+{c.puntos}</span>
            <div>
              <div className="regla">{c.regla}{c.gate ? ' · GATE' : ''}</div>
              <div className="ev">{c.evidencia}</div>
            </div>
          </li>
        ))}
      </ul>

      <div className="sello">{d.aviso}</div>
    </div>
  )
}
