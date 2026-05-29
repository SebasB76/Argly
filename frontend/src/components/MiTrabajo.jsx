import { useEffect, useState } from 'react'
import { getMiTrabajo } from '../api'
import { useArgly } from '../context/ArglyContext'
import { fmtMoney, fmtMoneyK, fmtNum } from '../lib/format'

const EST = [
  { id: 'sin_revisar', label: 'Sin revisar', cls: 'sr' },
  { id: 'en_revision', label: 'En revisión', cls: 'er' },
  { id: 'escalado', label: 'Escalado', cls: 'es' },
  { id: 'cerrado', label: 'Cerrado', cls: 'ce' },
]
const EV = {
  nota: '✎', veredicto: '⚖', estado: '↪',
}
const VER_TXT = { confirmado: 'Fraude confirmado', falso_positivo: 'Falso positivo', descartado: 'Descartado', pendiente: 'Pendiente' }
const EST_TXT = { sin_revisar: 'Sin revisar', en_revision: 'En revisión', escalado: 'Escalado', cerrado: 'Cerrado' }

function fechaCorta(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? '' : d.toLocaleString('es-EC', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false })
}
function evTexto(e) {
  if (e.tipo === 'veredicto') return `Veredicto → ${VER_TXT[e.valor] || e.valor}`
  if (e.tipo === 'estado') return `Estado → ${EST_TXT[e.valor] || e.valor}`
  return e.texto || 'Nota'
}

export default function MiTrabajo() {
  const { abrirCaso } = useArgly()
  const [t, setT] = useState(null)

  useEffect(() => { getMiTrabajo().then(setT).catch(() => {}) }, [])
  if (!t) return <div className="detalle vacio">Cargando tu tablero…</div>

  const pct = t.total ? Math.round((t.revisados / t.total) * 100) : 0
  const maxEstado = Math.max(...EST.map((e) => t.por_estado[e.id] || 0), 1)

  return (
    <div className="trabajo">
      <div className="sec-head">
        <span className="sec-eyebrow">Operación diaria</span>
        <h2 className="sec-title">Mi trabajo</h2>
      </div>

      {/* KPIs */}
      <div className="mt-kpis">
        <div className="mt-kpi"><b>{fmtNum(t.revisados)}<small>/{fmtNum(t.total)}</small></b><span>Revisados ({pct}%)</span></div>
        <div className="mt-kpi alerta"><b>{fmtNum(t.pendientes_rojos)}</b><span>Rojos sin revisar</span></div>
        <div className="mt-kpi ok"><b>{fmtNum(t.por_veredicto?.confirmado || 0)}</b><span>Fraudes confirmados</span></div>
        <div className="mt-kpi"><b>{fmtMoneyK(t.monto_confirmado)}</b><span>Monto confirmado</span></div>
        <div className="mt-kpi"><b>{fmtMoneyK(t.monto_escalado)}</b><span>Monto escalado</span></div>
      </div>

      {/* --- Mi cola: qué revisar ahora --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Mi cola</span>
          <h3>Qué revisar ahora</h3>
        </div>
        <div className="overview-grid">
          {/* Pendientes prioritarios */}
          <div className="chartcard span2">
            <div className="cc-head"><div><div className="cc-title">Pendientes prioritarios</div><div className="cc-sub">Rojos sin revisar, por impacto (riesgo × monto)</div></div></div>
            {t.pendientes_top.length === 0
              ? <div className="mt-empty">🎉 No hay rojos pendientes. ¡Bandeja al día!</div>
              : (
                <ul className="mt-pend">
                  {t.pendientes_top.map((c) => (
                    <li key={c.id_siniestro} onClick={() => abrirCaso(c.id_siniestro)}>
                      <span className="mt-score">{c.score}</span>
                      <div className="mt-pend-body">
                        <div className="mt-pend-top"><b className="mono">{c.id_siniestro}</b><span>{c.sucursal}</span></div>
                        <div className="mt-pend-motivo">{c.motivo_principal}</div>
                      </div>
                      <span className="mono mt-pend-monto">{fmtMoney(c.monto_reclamado)}</span>
                    </li>
                  ))}
                </ul>
              )}
          </div>

          {/* Estado de la cola */}
          <div className="chartcard">
            <div className="cc-head"><div><div className="cc-title">Estado de la cola</div><div className="cc-sub">Distribución de gestión</div></div></div>
            <div className="mt-estados">
              {EST.map((e) => {
                const v = t.por_estado[e.id] || 0
                return (
                  <div key={e.id} className="mt-est-row">
                    <span className={`est-badge ${e.cls}`}>{e.label}</span>
                    <div className="mt-est-bar"><i className={e.cls} style={{ width: `${(v / maxEstado) * 100}%` }} /></div>
                    <span className="mono mt-est-n">{v}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {/* --- Novedades: qué está pasando --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Novedades</span>
          <h3>Qué está pasando</h3>
        </div>
        <div className="overview-grid">
          {/* Proveedores en la mira */}
          <div className="chartcard">
            <div className="cc-head"><div><div className="cc-title">Proveedores en la mira</div><div className="cc-sub">Concentran más alertas</div></div></div>
            <ul className="mt-prov">
              {(t.proveedores_top || []).map((p) => (
                <li key={p.id_proveedor}>
                  <span className="mono">{p.id_proveedor}</span>
                  <span className="mt-prov-a">{p.alertas} alertas</span>
                  <span className="mono mt-prov-m">{fmtMoneyK(p.monto)}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Actividad reciente / novedades */}
          <div className="chartcard span2">
            <div className="cc-head"><div><div className="cc-title">Actividad reciente</div><div className="cc-sub">Lo último que se registró en la operación</div></div></div>
            {(!t.actividad_reciente || t.actividad_reciente.length === 0)
              ? <div className="mt-empty">Aún no hay actividad registrada.</div>
              : (
                <ul className="mt-acti">
                  {t.actividad_reciente.map((e, i) => (
                    <li key={i} onClick={() => abrirCaso(e.id_siniestro)} className={e.tipo}>
                      <span className="mt-acti-ic">{EV[e.tipo] || '•'}</span>
                      <span className="mono mt-acti-id">{e.id_siniestro}</span>
                      <span className="mt-acti-tx">{evTexto(e)}</span>
                      <span className="mt-acti-fe">{fechaCorta(e.fecha)}</span>
                    </li>
                  ))}
                </ul>
              )}
          </div>
        </div>
      </section>
    </div>
  )
}
