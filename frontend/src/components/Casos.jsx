import { useEffect, useState } from 'react'
import { getCasos } from '../api'
import { useArgly } from '../context/ArglyContext'
import Bandeja from './Bandeja'
import Detalle from './Detalle'
import Scorear from './Scorear'

const NIVELES = ['TODOS', 'ROJO', 'AMARILLO', 'VERDE']

export default function Casos() {
  const { casoSel, setCasoSel, fetchCaso } = useArgly()
  const [casos, setCasos] = useState([])
  const [filtro, setFiltro] = useState('TODOS')
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [tab, setTab] = useState('detalle') // 'detalle' | 'score'

  useEffect(() => {
    setCargando(true)
    getCasos(filtro === 'TODOS' ? null : filtro, 200)
      .then((d) => setCasos(d.casos || []))
      .catch(() => setCasos([]))
      .finally(() => setCargando(false))
  }, [filtro])

  // Abrir un caso solicitado desde el chat (tarjeta → "Abrir en Casos")
  useEffect(() => {
    if (!casoSel) return
    fetchCaso(casoSel).then((d) => { setDetalle(d); setTab('detalle') }).catch(() => {})
    setCasoSel(null)
  }, [casoSel, fetchCaso, setCasoSel])

  const abrir = (id) => { fetchCaso(id).then((d) => setDetalle(d)).catch(() => {}); setTab('detalle') }

  return (
    <div className="content">
      <section className="left">
        <div className="sec-head">
          <span className="sec-eyebrow">Bandeja priorizada</span>
          <h2 className="sec-title">Most Wanted</h2>
          <div className="filtros">
            {NIVELES.map((nv) => (
              <button key={nv} className={`f ${filtro === nv ? 'on' : ''}`} onClick={() => setFiltro(nv)}>{nv}</button>
            ))}
          </div>
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
          {tab === 'detalle' && <div className="detalle-panel"><Detalle d={detalle} onClose={() => setDetalle(null)} /></div>}
          {tab === 'score' && <div className="score-panel"><Scorear /></div>}
        </div>
      </section>
    </div>
  )
}
