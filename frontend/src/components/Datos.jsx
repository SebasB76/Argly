import { useEffect, useRef, useState } from 'react'
import { getDataset, importarDataset, resetDataset, getFeedback, reentrenar, URL_REPORTE_PDF, URL_REPORTE_EXCEL } from '../api'

const TABLAS = [
  { id: 'siniestros', label: 'Siniestros', req: true },
  { id: 'polizas', label: 'Pólizas' },
  { id: 'proveedores', label: 'Proveedores' },
  { id: 'asegurados', label: 'Asegurados' },
  { id: 'vehiculos', label: 'Vehículos' },
  { id: 'documentos', label: 'Documentos' },
]

const ORIGEN = { sintetico: 'Sintético (demo)', importado: 'Importado' }
const MODO = { hibrido: 'Híbrido (reglas + ML)', solo_reglas: 'Solo reglas (sin etiquetas)' }

export default function Datos() {
  const [ds, setDs] = useState(null)
  const [archivos, setArchivos] = useState({})
  const [modo, setModo] = useState('replace')
  const [estado, setEstado] = useState(null) // {tipo:'ok'|'err', msg}
  const [cargando, setCargando] = useState(false)
  const [verCols, setVerCols] = useState(false)
  const inputs = useRef({})

  const [fb, setFb] = useState(null)
  const [reent, setReent] = useState(null)
  const [reentrenando, setReentrenando] = useState(false)

  const refrescar = () => {
    getDataset().then(setDs).catch(() => {})
    getFeedback().then(setFb).catch(() => {})
  }
  useEffect(() => { refrescar() }, [])

  const lanzarReentrenamiento = async () => {
    setReentrenando(true)
    try {
      const r = await reentrenar()
      setReent(r)
      refrescar()
    } catch { setReent({ error: true }) } finally { setReentrenando(false) }
  }

  const elegir = (tabla, file) => setArchivos((p) => ({ ...p, [tabla]: file }))

  const limpiar = () => {
    setArchivos({})
    Object.values(inputs.current).forEach((el) => { if (el) el.value = '' })
  }

  const importar = async () => {
    if (!archivos.siniestros) {
      setEstado({ tipo: 'err', msg: 'Debes seleccionar al menos la tabla "siniestros".' })
      return
    }
    setCargando(true)
    setEstado(null)
    try {
      const r = await importarDataset(archivos, modo)
      setDs(r.dataset)
      const ins = r.insertados
      const detalle = ins
        ? ` (${Object.entries(ins).filter(([, n]) => n > 0).map(([t, n]) => `${n} ${t}`).join(', ') || 'sin filas nuevas'})`
        : ''
      setEstado({ tipo: 'ok', msg: `Dataset ${modo === 'append' ? 'anexado' : 'reemplazado'}${detalle}. Pipeline recalculado.` })
      limpiar()
    } catch (e) {
      setEstado({ tipo: 'err', msg: e.message || 'Error al importar.' })
    } finally {
      setCargando(false)
    }
  }

  const reset = async () => {
    setCargando(true)
    setEstado(null)
    try {
      const r = await resetDataset()
      setDs(r.dataset)
      setEstado({ tipo: 'ok', msg: 'Dataset restaurado al sintético de demo.' })
      limpiar()
    } catch {
      setEstado({ tipo: 'err', msg: 'No se pudo restaurar.' })
    } finally {
      setCargando(false)
    }
  }

  const c = ds?.conteos || {}

  return (
    <div className="datos">
      <div className="sec-head">
        <span className="sec-eyebrow">Gestión de datos</span>
        <h2 className="sec-title">Dataset</h2>
      </div>
      <p className="datos-intro">
        Argly usa la base de datos como fuente de verdad. Acá ves el dataset activo, lo
        <b> reemplazas o anexas</b> con datos propios, <b>reentrenas</b> el modelo con el feedback
        del analista y <b>exportas</b> reportes para dirección y auditoría.
      </p>

      {/* --- Estado actual --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Estado actual</span>
          <h3>Dataset activo</h3>
        </div>
        <div className="panel ds-estado">
          <div className="ds-row">
            <div className="ds-kpi">
              <span className="ds-k">Origen</span>
              <b className={`ds-badge ${ds?.origen || ''}`}>{ORIGEN[ds?.origen] || '—'}</b>
            </div>
            <div className="ds-kpi">
              <span className="ds-k">Modo de scoring</span>
              <b>{MODO[ds?.modo] || '—'}</b>
            </div>
            <div className="ds-kpi">
              <span className="ds-k">Siniestros</span>
              <b>{(ds?.n_siniestros ?? 0).toLocaleString('es-EC')}</b>
            </div>
            <div className="ds-kpi">
              <span className="ds-k">Train / Test</span>
              <b>{ds?.n_train ?? 0} / {ds?.n_test ?? 0}</b>
            </div>
            <div className="ds-kpi">
              <span className="ds-k">Etiquetados fraude</span>
              <b>{ds?.casos_etiquetados_fraude ?? 0}</b>
            </div>
          </div>
          <div className="ds-conteos">
            {TABLAS.map((t) => (
              <span key={t.id} className="ds-chip"><i>{t.label}</i> {(c[t.id] ?? 0).toLocaleString('es-EC')}</span>
            ))}
          </div>
          {ds?.modo === 'solo_reglas' && (
            <div className="ds-nota">El dataset no tiene etiquetas de fraude usables: Argly puntúa con el motor de reglas (el ML queda fuera hasta que haya casos etiquetados).</div>
          )}
        </div>
      </section>

      {/* --- Importar y exportar --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Administrar</span>
          <h3>Importar y exportar</h3>
        </div>
        <div className="datos-grid">
          <div className="panel ds-import">
            <div className="scorear-h">Importar dataset</div>
            <p className="ds-help">
              Sube uno o más CSV (uno por tabla). Solo <b>siniestros</b> es obligatorio; las
              tablas que falten se completan con valores por defecto.
            </p>

            <div className="ds-modo">
              <label className={modo === 'replace' ? 'on' : ''}>
                <input type="radio" name="modo" checked={modo === 'replace'} onChange={() => setModo('replace')} />
                <span><b>Reemplazar</b><i>sustituye todo el dataset</i></span>
              </label>
              <label className={modo === 'append' ? 'on' : ''}>
                <input type="radio" name="modo" checked={modo === 'append'} onChange={() => setModo('append')} />
                <span><b>Anexar</b><i>agrega casos (omite IDs repetidos)</i></span>
              </label>
            </div>

            <div className="ds-files">
              {TABLAS.map((t) => (
                <label key={t.id} className={`ds-file ${archivos[t.id] ? 'has' : ''}`}>
                  <span className="ds-file-name">{t.label}{t.req && <em> *</em>}</span>
                  <input
                    ref={(el) => { inputs.current[t.id] = el }}
                    type="file" accept=".csv,text/csv"
                    onChange={(e) => elegir(t.id, e.target.files?.[0] || null)}
                  />
                  <span className="ds-file-pick">{archivos[t.id]?.name || 'Elegir CSV…'}</span>
                </label>
              ))}
            </div>

            <div className="scorear-btns">
              <button onClick={importar} disabled={cargando}>{cargando ? '…' : 'Importar'}</button>
              <button className="preset" onClick={reset} disabled={cargando}>Restaurar sintético</button>
              <button className="preset" type="button" onClick={() => setVerCols((v) => !v)}>
                {verCols ? 'Ocultar columnas' : 'Ver columnas esperadas'}
              </button>
            </div>

            {estado && <div className={`ds-msg ${estado.tipo}`}>{estado.msg}</div>}

            {verCols && ds?.columnas_esperadas && (
              <div className="ds-cols">
                {TABLAS.map((t) => (
                  <div key={t.id} className="ds-col-tabla">
                    <b>{t.label}</b>
                    <code>{(ds.columnas_esperadas[t.id] || []).join(', ')}</code>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel ds-reportes">
            <div className="scorear-h">Reporte ejecutivo</div>
            <p className="ds-help">
              Resumen consolidado para dirección y auditoría: panorama, casos de mayor riesgo,
              Pareto de proveedores, distribución, equidad y métricas.
            </p>
            <div className="rep-btns">
              <a className="rep-btn pdf" href={URL_REPORTE_PDF} target="_blank" rel="noreferrer">
                <span className="rep-ic">PDF</span>
                <span>Reporte ejecutivo<i>abrir / imprimir</i></span>
              </a>
              <a className="rep-btn xls" href={URL_REPORTE_EXCEL}>
                <span className="rep-ic">XLS</span>
                <span>Bandeja en Excel<i>descargar · multi-hoja</i></span>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* --- Aprendizaje del modelo --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Human-in-the-loop</span>
          <h3>Aprendizaje del modelo</h3>
        </div>
        <div className="panel ds-aprendizaje">
          <p className="ds-help">
            Los veredictos del analista (en el dossier de cada caso) son etiquetas de
            verdad. <b>Reentrenar</b> las incorpora y mide el efecto sobre el test held-out.
          </p>
          <div className="apz-fb">
            <span className="apz-chip"><i>Confirmados</i> {fb?.por_veredicto?.confirmado ?? 0}</span>
            <span className="apz-chip"><i>Falsos pos.</i> {fb?.por_veredicto?.falso_positivo ?? 0}</span>
            <span className="apz-chip"><i>Descartados</i> {fb?.por_veredicto?.descartado ?? 0}</span>
            <span className="apz-chip total"><i>Etiquetas</i> {fb?.etiquetas_disponibles ?? 0}</span>
          </div>
          <div className="scorear-btns">
            <button onClick={lanzarReentrenamiento} disabled={reentrenando}>
              {reentrenando ? 'Reentrenando…' : 'Reentrenar con feedback'}
            </button>
          </div>
          {reent && reent.error && <div className="ds-msg err">No se pudo reentrenar.</div>}
          {reent && !reent.error && (
            <div className="apz-res">
              <div className="apz-res-h">{reent.feedback_aplicado} etiqueta(s) de analista aplicada(s)</div>
              {reent.antes && reent.despues ? (
                <table className="apz-tabla">
                  <thead><tr><th>Métrica</th><th>Antes</th><th>Después</th><th>Δ</th></tr></thead>
                  <tbody>
                    {[['AUC híbrido', 'auc_hibrido'], ['AUC ML', 'auc_ml'], ['Precisión', 'precision'], ['Recall', 'recall'], ['F1', 'f1']].map(([label, k]) => {
                      const a = reent.antes[k], d = reent.despues[k]
                      const delta = (a != null && d != null) ? +(d - a).toFixed(3) : null
                      return (
                        <tr key={k}>
                          <td>{label}</td><td>{a ?? '—'}</td><td>{d ?? '—'}</td>
                          <td className={delta > 0 ? 'up' : delta < 0 ? 'down' : ''}>
                            {delta == null ? '—' : (delta > 0 ? `+${delta}` : delta)}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              ) : (
                <div className="ds-nota">Aún no hay etiquetas suficientes (de analista o del dataset) para entrenar el ML y comparar métricas. Marca casos como confirmado/falso positivo y reentrena.</div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
