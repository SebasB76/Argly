import { useCallback, useEffect, useState } from 'react'
import { useArgly } from '../../context/ArglyContext'
import { fmtMoney } from '../../lib/format'
import { API_BASE } from '../../api'

export default function CasoCard({ id, seed = {}, autoload = false }) {
  const { fetchCaso, abrirCaso } = useArgly()
  const [full, setFull] = useState(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(false)

  const cargar = useCallback(() => {
    if (full) return Promise.resolve(full)
    setLoading(true); setErr(false)
    return fetchCaso(id)
      .then((d) => { setFull(d); return d })
      .catch(() => { setErr(true); return null })
      .finally(() => setLoading(false))
  }, [id, full, fetchCaso])

  useEffect(() => { if (autoload) cargar() }, [autoload, cargar])

  const score = full?.score ?? seed.score
  const nivel = full?.nivel ?? seed.nivel ?? 'verde'
  const nivelLow = String(nivel).toLowerCase()
  const subtitle = full?.recomendacion || seed.motivo || 'Cargando…'
  const contribs = full ? [...(full.contribuciones || [])].sort((a, b) => b.puntos - a.puntos) : []

  const toggle = () => { if (!open && !full) cargar(); setOpen((o) => !o) }

  return (
    <div className={`casocard ${nivelLow} ${open ? 'open' : ''}`}>
      <div className="cck-head">
        <div className="cck-gauge">
          <span className="cck-score">{score ?? '··'}</span>
          <span className="cck-cap">SCORE</span>
        </div>
        <div className="cck-id">
          <span className="mono cck-sin">{id}</span>
          <span className="cck-nivel">{String(nivel).toUpperCase()}</span>
        </div>
        {seed.monto != null && !open && <span className="cck-monto mono">{fmtMoney(seed.monto)}</span>}
      </div>

      <div className="cck-sub">{subtitle}</div>

      {!open && contribs.length > 0 && (
        <ul className="cck-mini">
          {contribs.slice(0, 2).map((c, i) => (
            <li key={i} className={c.gate ? 'gate' : ''}>
              <span className="pts">+{c.puntos}</span>
              <span className="rg">{c.regla}{c.gate ? ' · GATE ⚠' : ''}</span>
            </li>
          ))}
        </ul>
      )}

      {open && full && (
        <div className="cck-full">
          <div className="cck-meta mono">{full.ramo} · {full.cobertura} · {full.sucursal} · {fmtMoney(full.monto_reclamado)}</div>
          <div className="contrib-h">Por qué · {contribs.length} señales</div>
          <ul className="contribs">
            {contribs.map((c, i) => (
              <li key={i} className={c.gate ? 'gate' : ''} style={{ animationDelay: `${i * 40}ms` }}>
                <span className="pts">+{c.puntos}</span>
                <div>
                  <div className="regla">{c.regla}{c.gate ? ' · GATE' : ''}</div>
                  <div className="ev">{c.evidencia}</div>
                </div>
              </li>
            ))}
          </ul>
          {full.aviso && <div className="sello">{full.aviso}</div>}
          <div className="cck-actions">
            <a className="pdf-btn" href={`${API_BASE}/casos/${id}/dossier`} target="_blank" rel="noreferrer">↓ PDF</a>
            <button className="cck-open" onClick={() => abrirCaso(id)}>Abrir en Casos →</button>
          </div>
        </div>
      )}

      <button className="cck-toggle" onClick={toggle} disabled={loading}>
        {loading ? 'Cargando dossier…' : open ? '▴ Ocultar dossier' : 'Ver dossier completo →'}
      </button>
      {err && <div className="cck-err">No pude cargar el dossier de {id}.</div>}
    </div>
  )
}
