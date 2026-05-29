import { useEffect, useState } from 'react'
import { enviarFeedback, getContrafactual, setEstado, getVinculos, getBitacora, agregarNota, getChecklist, setChecklistPaso, API_BASE } from '../api'

const EVENTO = {
  nota: { ic: '✎', txt: () => 'Nota' },
  veredicto: { ic: '⚖', txt: (e) => `Veredicto → ${({ confirmado: 'Fraude confirmado', falso_positivo: 'Falso positivo', descartado: 'Descartado', pendiente: 'Pendiente' })[e.valor] || e.valor}` },
  estado: { ic: '↪', txt: (e) => `Estado → ${({ sin_revisar: 'Sin revisar', en_revision: 'En revisión', escalado: 'Escalado', cerrado: 'Cerrado' })[e.valor] || e.valor}` },
}

function fechaCorta(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleString('es-EC', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false })
}

const VINCULOS = [
  { id: 'mismo_proveedor', label: 'Mismo proveedor' },
  { id: 'mismo_asegurado', label: 'Mismo asegurado' },
  { id: 'mismo_conductor', label: 'Mismo conductor' },
  { id: 'misma_placa', label: 'Misma placa' },
  { id: 'narrativa_similar', label: 'Narrativa similar' },
]

const ESTADOS = [
  { id: 'sin_revisar', label: 'Sin revisar' },
  { id: 'en_revision', label: 'En revisión' },
  { id: 'escalado', label: 'Escalado' },
  { id: 'cerrado', label: 'Cerrado' },
]

const VEREDICTOS = [
  { id: 'confirmado', label: 'Confirmar fraude', cls: 'rojo' },
  { id: 'falso_positivo', label: 'Falso positivo', cls: 'verde' },
  { id: 'descartado', label: 'Descartar', cls: 'amarillo' },
]
const ETIQUETA_VER = {
  confirmado: 'Fraude confirmado', falso_positivo: 'Falso positivo',
  descartado: 'Descartado', pendiente: 'Pendiente de revisión',
}
const ETIQUETA_EST = {
  sin_revisar: 'Sin revisar', en_revision: 'En revisión', escalado: 'Escalado', cerrado: 'Cerrado',
}

// Sección colapsable del dossier (acordeón) con contador en la cabecera.
function Seccion({ titulo, badge, abierto = false, children }) {
  const [open, setOpen] = useState(abierto)
  return (
    <div className={`dz-sec ${open ? 'open' : ''}`}>
      <button type="button" className="dz-head" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className="dz-chev" aria-hidden>▸</span>
        <span className="dz-titulo">{titulo}</span>
        {badge != null && <span className="dz-badge">{badge}</span>}
      </button>
      {open && <div className="dz-body">{children}</div>}
    </div>
  )
}

export default function Detalle({ d, onClose, onFeedback, onOpen }) {
  const [enviando, setEnviando] = useState(null)
  const [cf, setCf] = useState(null)
  const [vinc, setVinc] = useState(null)
  const [bita, setBita] = useState([])
  const [nota, setNota] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [chk, setChk] = useState(null)

  // Contrafactual: solo para casos que no están en VERDE
  useEffect(() => {
    setCf(null)
    if (d && d.nivel !== 'VERDE') {
      getContrafactual(d.id_siniestro).then(setCf).catch(() => {})
    }
  }, [d?.id_siniestro, d?.nivel])

  // Casos vinculados
  useEffect(() => {
    setVinc(null)
    if (d) getVinculos(d.id_siniestro).then(setVinc).catch(() => {})
  }, [d?.id_siniestro])

  // Bitácora del caso
  const recargarBitacora = () => { if (d) getBitacora(d.id_siniestro).then((r) => setBita(r.bitacora || [])).catch(() => {}) }
  useEffect(() => {
    setBita([]); setNota('')
    recargarBitacora()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d?.id_siniestro])

  // Checklist de investigación
  useEffect(() => {
    setChk(null)
    if (d) getChecklist(d.id_siniestro).then(setChk).catch(() => {})
  }, [d?.id_siniestro])

  const togglePaso = async (clave, hecho) => {
    try { setChk(await setChecklistPaso(d.id_siniestro, clave, hecho)) } catch { /* noop */ }
  }

  if (!d) return <div className="detalle vacio">Selecciona una señal de la bandeja para abrir su dossier.</div>

  const nivel = d.nivel.toLowerCase()
  const contribs = [...(d.contribuciones || [])].sort((a, b) => b.puntos - a.puntos)
  const veredicto = d.feedback?.veredicto || 'pendiente'

  const marcar = async (v) => {
    setEnviando(v)
    try {
      const r = await enviarFeedback(d.id_siniestro, v)
      onFeedback?.(d.id_siniestro, r.feedback)
      recargarBitacora()
    } catch { /* noop */ } finally { setEnviando(null) }
  }

  const cambiarEstado = async (e) => {
    try {
      const r = await setEstado(d.id_siniestro, e)
      onFeedback?.(d.id_siniestro, r.feedback)
      recargarBitacora()
    } catch { /* noop */ }
  }

  const guardarNota = async () => {
    if (!nota.trim()) return
    setGuardando(true)
    try {
      const r = await agregarNota(d.id_siniestro, nota.trim())
      setBita(r.bitacora || [])
      setNota('')
    } catch { /* noop */ } finally { setGuardando(false) }
  }
  const estado = d.feedback?.estado || 'sin_revisar'

  const totalVinc = VINCULOS.reduce((s, g) => s + (vinc?.[g.id]?.length || 0), 0)
  const hayVinc = vinc && totalVinc > 0
  const hayCf = cf && !cf.ya_verde && cf.cambios?.length > 0

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

      {d.resumen && <div className="caso-resumen"><span className="cr-tag">Resumen</span>{d.resumen}</div>}

      <div className="reco">{d.recomendacion}</div>
      <div className="meta">
        {d.ramo} · {d.cobertura} · {d.sucursal} · ${d.monto_reclamado.toLocaleString('es-EC', { maximumFractionDigits: 0 })}
      </div>
      <a className="pdf-btn" href={`${API_BASE}/casos/${d.id_siniestro}/dossier`} target="_blank" rel="noreferrer">↓ Descargar dossier PDF</a>

      <div className="dz">
        {/* --- Señales (por qué) --- */}
        <Seccion key="senales" titulo="Señales detectadas" badge={contribs.length} abierto>
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
        </Seccion>

        {/* --- Decisión y gestión (qué hacer) --- */}
        <Seccion key="decision" titulo="Decisión y gestión"
          badge={<span className={`dz-est ${estado}`}>{ETIQUETA_EST[estado]}</span>} abierto>
          <div className="dz-sub">Estado de gestión</div>
          <div className="est-seg">
            {ESTADOS.map((e) => (
              <button key={e.id} className={`est-opt ${e.id} ${estado === e.id ? 'on' : ''}`}
                onClick={() => cambiarEstado(e.id)}>{e.label}</button>
            ))}
          </div>
          <div className="dz-sub" style={{ marginTop: 14 }}>
            Veredicto <span className={`vb-badge ${veredicto}`}>{ETIQUETA_VER[veredicto]}</span>
          </div>
          <div className="vb-btns">
            {VEREDICTOS.map((v) => (
              <button key={v.id} className={`vb ${v.cls} ${veredicto === v.id ? 'on' : ''}`}
                onClick={() => marcar(v.id)} disabled={enviando}>{enviando === v.id ? '…' : v.label}</button>
            ))}
          </div>
          <div className="vb-hint">Tu veredicto alimenta el reentrenamiento del modelo (vista Datos → Aprendizaje).</div>
        </Seccion>

        {/* --- Investigación (checklist) --- */}
        {chk && chk.pasos?.length > 0 && (
          <Seccion key="investigacion" titulo="Investigación"
            badge={<>{chk.completados}/{chk.total}{chk.listo_para_escalar && <i className="dz-ok"> ✓ listo</i>}</>}>
            <div className="chk-prog"><i style={{ width: `${chk.total ? (chk.completados / chk.total) * 100 : 0}%` }} /></div>
            <ul className="chk-list">
              {chk.pasos.map((p) => (
                <li key={p.clave} className={p.hecho ? 'done' : ''}>
                  <label>
                    <input type="checkbox" checked={p.hecho} onChange={(e) => togglePaso(p.clave, e.target.checked)} />
                    <span>{p.label}{p.requerido && <i className="chk-req">requerido</i>}</span>
                  </label>
                </li>
              ))}
            </ul>
          </Seccion>
        )}

        {/* --- Casos vinculados --- */}
        {hayVinc && (
          <Seccion key="vinculos" titulo="Casos vinculados" badge={totalVinc}>
            {VINCULOS.map((g) => {
              const items = vinc[g.id] || []
              if (!items.length) return null
              return (
                <div key={g.id} className="vinc-grupo">
                  <div className="vinc-lbl">{g.label} <span>{items.length}</span></div>
                  <ul className="vinc-list">
                    {items.map((it) => (
                      <li key={it.id_siniestro} className={it.nivel.toLowerCase()} onClick={() => onOpen?.(it.id_siniestro)}>
                        <span className="vl-score">{it.score}</span>
                        <span className="vl-id mono">{it.id_siniestro}</span>
                        <span className="vl-motivo">{it.motivo_principal}{it.similitud != null ? ` · ${Math.round(it.similitud * 100)}% sim.` : ''}</span>
                        <span className="vl-monto mono">${it.monto_reclamado.toLocaleString('es-EC', { maximumFractionDigits: 0 })}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </Seccion>
        )}

        {/* --- Contrafactual --- */}
        {hayCf && (
          <Seccion key="contrafactual" titulo="¿Qué bajaría el riesgo?"
            badge={<span className="cf-proy">→ ~{cf.score_proyectado} <b className={cf.nivel_proyectado?.toLowerCase()}>{cf.nivel_proyectado}</b></span>}>
            <ul className="cf-list">
              {cf.cambios.map((c, i) => (
                <li key={i} className={c.gate ? 'gate' : ''}>
                  <span className="cf-pts">−{c.puntos}</span>
                  <span className="cf-accion">{c.accion}{c.gate ? ' · GATE' : ''}</span>
                </li>
              ))}
            </ul>
            <div className="cf-hint">{cf.resumen}</div>
          </Seccion>
        )}

        {/* --- Actividad / bitácora --- */}
        <Seccion key="actividad" titulo="Actividad" badge={bita.length}>
          <div className="acti-nueva">
            <textarea value={nota} onChange={(e) => setNota(e.target.value)} rows={2}
              placeholder="Añadir una nota (ej. llamé al asegurado, pedí la factura original…)" />
            <button onClick={guardarNota} disabled={guardando || !nota.trim()}>{guardando ? '…' : 'Agregar nota'}</button>
          </div>
          {bita.length === 0 ? (
            <div className="acti-vacia">Sin actividad registrada todavía.</div>
          ) : (
            <ul className="acti-list">
              {[...bita].reverse().map((e) => {
                const cfg = EVENTO[e.tipo] || EVENTO.nota
                return (
                  <li key={e.id} className={`acti ${e.tipo}`}>
                    <span className="acti-ic">{cfg.ic}</span>
                    <div className="acti-body">
                      <div className="acti-top"><b>{cfg.txt(e)}</b><span>{fechaCorta(e.fecha)}</span></div>
                      {e.texto && <div className="acti-txt">{e.texto}</div>}
                      <div className="acti-autor">{e.autor}</div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </Seccion>
      </div>

      <div className="sello">{d.aviso}</div>
    </div>
  )
}
