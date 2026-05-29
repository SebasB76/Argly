import { useEffect, useMemo, useRef, useState } from 'react'
import { getCasos } from '../api'
import { useArgly } from '../context/ArglyContext'
import Bandeja from './Bandeja'
import Detalle from './Detalle'
import Scorear from './Scorear'

const NIVELES = ['TODOS', 'ROJO', 'AMARILLO', 'VERDE']
const ESTADOS = [
  { id: '', label: 'Todos los estados' },
  { id: 'sin_revisar', label: 'Sin revisar' },
  { id: 'en_revision', label: 'En revisión' },
  { id: 'escalado', label: 'Escalado' },
  { id: 'cerrado', label: 'Cerrado' },
]
const VACIO = {
  nivel: 'TODOS', estado: '', ramo: '', ciudad: '', q: '',
  monto_min: '', monto_max: '', score_min: '', score_max: '', orden: 'score',
}
const VISTAS_KEY = 'argly_vistas'

// Filtros que se muestran como chips removibles (los avanzados; nivel/orden/q van aparte)
const CHIP_DEFS = [
  { key: 'estado', etq: (v) => `Estado: ${ESTADOS.find((e) => e.id === v)?.label || v}` },
  { key: 'ramo', etq: (v) => `Ramo: ${v}` },
  { key: 'ciudad', etq: (v) => `Ciudad: ${v}` },
  { key: 'monto_min', etq: (v) => `Monto ≥ $${Number(v).toLocaleString('es-EC')}` },
  { key: 'monto_max', etq: (v) => `Monto ≤ $${Number(v).toLocaleString('es-EC')}` },
  { key: 'score_min', etq: (v) => `Score ≥ ${v}` },
]

function cargarVistas() {
  try { return JSON.parse(localStorage.getItem(VISTAS_KEY)) || [] } catch { return [] }
}

export default function Casos() {
  const { casoSel, setCasoSel, fetchCaso, invalidarCaso } = useArgly()
  const [casos, setCasos] = useState([])
  const [filtros, setFiltros] = useState(VACIO)
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [tab, setTab] = useState('detalle')
  const [opciones, setOpciones] = useState({ ramos: [], ciudades: [] })
  const [vistas, setVistas] = useState(cargarVistas)
  const [abierto, setAbierto] = useState(false)        // filtros avanzados desplegados
  const debounce = useRef(null)

  const set = (k, v) => setFiltros((p) => ({ ...p, [k]: v }))

  // Opciones de ramo/ciudad (una sola vez, sobre toda la bandeja)
  useEffect(() => {
    getCasos({ limit: 3000 }).then((d) => {
      const cs = d.casos || []
      setOpciones({
        ramos: [...new Set(cs.map((c) => c.ramo))].filter(Boolean).sort(),
        ciudades: [...new Set(cs.map((c) => c.sucursal))].filter(Boolean).sort(),
      })
    }).catch(() => {})
  }, [])

  const recargar = (f = filtros) => {
    setCargando(true)
    getCasos({ ...f, limit: 300 })
      .then((d) => setCasos(d.casos || []))
      .catch(() => setCasos([]))
      .finally(() => setCargando(false))
  }

  // Refetch al cambiar filtros (con debounce para la búsqueda de texto)
  useEffect(() => {
    clearTimeout(debounce.current)
    debounce.current = setTimeout(() => recargar(filtros), 250)
    return () => clearTimeout(debounce.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  // Abrir un caso solicitado desde el chat
  useEffect(() => {
    if (!casoSel) return
    fetchCaso(casoSel).then((d) => { setDetalle(d); setTab('detalle') }).catch(() => {})
    setCasoSel(null)
  }, [casoSel, fetchCaso, setCasoSel])

  const abrir = (id) => { fetchCaso(id).then((d) => setDetalle(d)).catch(() => {}); setTab('detalle') }

  // Tras feedback o cambio de estado: refleja en el dossier, invalida cache y refresca la lista
  const onActualizar = (id, feedback) => {
    setDetalle((prev) => (prev && prev.id_siniestro === id ? { ...prev, feedback } : prev))
    invalidarCaso(id)
    recargar()
  }

  const filtrosActivos = useMemo(
    () => Object.keys(VACIO).filter((k) => k !== 'orden' && filtros[k] && filtros[k] !== 'TODOS').length,
    [filtros],
  )
  const chips = CHIP_DEFS.filter((c) => filtros[c.key])
  const limpiarAvanzados = () => setFiltros((p) => ({ ...VACIO, q: p.q, nivel: p.nivel, orden: p.orden }))

  const guardarVista = () => {
    const nombre = window.prompt('Nombre de la vista:')
    if (!nombre) return
    const next = [...vistas.filter((v) => v.nombre !== nombre), { nombre, filtros }]
    setVistas(next)
    localStorage.setItem(VISTAS_KEY, JSON.stringify(next))
  }
  const aplicarVista = (v) => setFiltros({ ...VACIO, ...v.filtros })
  const borrarVista = (nombre) => {
    const next = vistas.filter((v) => v.nombre !== nombre)
    setVistas(next)
    localStorage.setItem(VISTAS_KEY, JSON.stringify(next))
  }

  return (
    <div className="content">
      <section className="left">
        <div className="sec-head">
          <span className="sec-eyebrow">Cola de trabajo</span>
          <h2 className="sec-title">Bandeja priorizada</h2>
        </div>

        {/* --- Barra de filtros --- */}
        <div className="filtros-bar">
          <div className="fb-row1">
            <div className="fb-search-wrap">
              <span className="fb-ic" aria-hidden>⌕</span>
              <input className="fb-search" placeholder="Buscar siniestro, asegurado o proveedor…"
                value={filtros.q} onChange={(e) => set('q', e.target.value)} />
              {filtros.q && <button className="fb-x" onClick={() => set('q', '')} aria-label="Limpiar búsqueda">×</button>}
            </div>
            <button className={`fb-toggle ${abierto ? 'on' : ''}`} onClick={() => setAbierto((v) => !v)}>
              ⚙ Filtros{filtrosActivos ? ` · ${filtrosActivos}` : ''}
            </button>
          </div>

          <div className="fb-row2">
            <div className="filtros">
              {NIVELES.map((nv) => (
                <button key={nv} className={`f ${filtros.nivel === nv ? 'on' : ''}`} onClick={() => set('nivel', nv)}>{nv}</button>
              ))}
            </div>
            <label className="fb-orden">
              <select value={filtros.orden} onChange={(e) => set('orden', e.target.value)}>
                <option value="score">↓ Por riesgo</option>
                <option value="impacto">↓ Por impacto $</option>
              </select>
            </label>
          </div>

          {(chips.length > 0 || vistas.length > 0) && (
            <div className="fb-chips-row">
              {chips.map((c) => (
                <span key={c.key} className="fb-fchip">{c.etq(filtros[c.key])}<i onClick={() => set(c.key, '')} title="Quitar">×</i></span>
              ))}
              {chips.length > 0 && <button className="fb-limpiar" onClick={limpiarAvanzados}>limpiar</button>}
              {vistas.length > 0 && <span className="fb-sep" />}
              {vistas.map((v) => (
                <span key={v.nombre} className="fb-chip">
                  <button onClick={() => aplicarVista(v)}>★ {v.nombre}</button>
                  <i onClick={() => borrarVista(v.nombre)} title="Eliminar">×</i>
                </span>
              ))}
            </div>
          )}

          {abierto && (
            <div className="fb-adv">
              <label>Estado
                <select value={filtros.estado} onChange={(e) => set('estado', e.target.value)}>
                  {ESTADOS.map((e) => <option key={e.id} value={e.id}>{e.label}</option>)}
                </select></label>
              <label>Ramo
                <select value={filtros.ramo} onChange={(e) => set('ramo', e.target.value)}>
                  <option value="">Todos</option>
                  {opciones.ramos.map((r) => <option key={r} value={r}>{r}</option>)}
                </select></label>
              <label>Ciudad
                <select value={filtros.ciudad} onChange={(e) => set('ciudad', e.target.value)}>
                  <option value="">Todas</option>
                  {opciones.ciudades.map((c) => <option key={c} value={c}>{c}</option>)}
                </select></label>
              <label>Monto ≥
                <input type="number" value={filtros.monto_min} onChange={(e) => set('monto_min', e.target.value)} placeholder="0" /></label>
              <label>Monto ≤
                <input type="number" value={filtros.monto_max} onChange={(e) => set('monto_max', e.target.value)} placeholder="∞" /></label>
              <label>Score ≥
                <input type="number" value={filtros.score_min} onChange={(e) => set('score_min', e.target.value)} placeholder="0" /></label>
              <div className="fb-acts">
                <button className="fb-save" onClick={guardarVista}>★ Guardar vista</button>
                <button className="fb-clear" onClick={() => setFiltros(VACIO)}>Limpiar todo</button>
              </div>
            </div>
          )}
        </div>

        <div className="bandeja-wrap" style={{ flex: '1 1 auto', minHeight: 0 }}>
          <Bandeja casos={casos} cargando={cargando} onSelect={abrir} sel={detalle?.id_siniestro} />
        </div>
      </section>

      <section className="right">
        <div className="tabs">
          <button className={`tab ${tab === 'detalle' ? 'active' : ''}`} onClick={() => setTab('detalle')}>◎ Dossier</button>
          <button className={`tab ${tab === 'score' ? 'active' : ''}`} onClick={() => setTab('score')}>⚗ Simulador</button>
        </div>
        <div className="panel tabpanel">
          {tab === 'detalle' && <div className="detalle-panel"><Detalle d={detalle} onClose={() => setDetalle(null)} onFeedback={onActualizar} onOpen={abrir} /></div>}
          {tab === 'score' && <div className="score-panel"><Scorear /></div>}
        </div>
      </section>
    </div>
  )
}
