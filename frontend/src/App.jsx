import { useEffect, useState } from 'react'
import { getResumen, getCasos, getCaso } from './api'
import Stats from './components/Stats'
import Bandeja from './components/Bandeja'
import Detalle from './components/Detalle'
import Agente from './components/Agente'
import Scorear from './components/Scorear'
import Redes from './components/Redes'
import './App.css'

const NIVELES = ['TODOS', 'ROJO', 'AMARILLO', 'VERDE']

export default function App() {
  const [resumen, setResumen] = useState(null)
  const [casos, setCasos] = useState([])
  const [filtro, setFiltro] = useState('TODOS')
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [activeTab, setActiveTab] = useState('detalle') // 'detalle' | 'agente' | 'score'
  const [openRedes, setOpenRedes] = useState(false)

  useEffect(() => { getResumen().then(setResumen).catch(() => {}) }, [])

  useEffect(() => {
    setCargando(true)
    getCasos(filtro === 'TODOS' ? null : filtro, 200)
      .then((d) => setCasos(d.casos || []))
      .catch(() => setCasos([]))
      .finally(() => setCargando(false))
  }, [filtro])

  const abrir = (id) => getCaso(id).then(setDetalle).catch(() => {})

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">ARGLY <span>· Antifraude de Siniestros</span></div>
        <div className="top-actions">
          <div className="aviso">⚠ ALERTA para revisión humana · NO es una acusación de fraude</div>
          <button className="header-btn" onClick={() => setOpenRedes(true)}>Ver Redes Detectadas</button>
        </div>
      </header>

      <main className="main">
        <div className="kpis">
          <Stats resumen={resumen} />
        </div>

        <div className="content">
          <div className="left">
            <div className="filtros">
              {NIVELES.map((n) => (
                <button key={n} className={`f ${filtro === n ? 'on' : ''}`} onClick={() => setFiltro(n)}>{n}</button>
              ))}
            </div>

            <div className="bandeja-wrap">
              <Bandeja casos={casos} cargando={cargando} onSelect={abrir} sel={detalle?.id_siniestro} />
            </div>
          </div>

          <div className="right">
            <div className="tabs">
              <button className={`tab ${activeTab === 'detalle' ? 'active' : ''}`} onClick={() => setActiveTab('detalle')}>Detalles del Caso</button>
              <button className={`tab ${activeTab === 'agente' ? 'active' : ''}`} onClick={() => setActiveTab('agente')}>Chat con ARGLY (IA)</button>
              <button className={`tab ${activeTab === 'score' ? 'active' : ''}`} onClick={() => setActiveTab('score')}>Score Manual</button>
            </div>

            <div className="panel">
              {activeTab === 'detalle' && <div className="detalle-panel"> <Detalle d={detalle} onClose={() => setDetalle(null)} /> </div>}
              {activeTab === 'agente' && <div className="agente-panel"> <Agente /> </div>}
              {activeTab === 'score' && <div className="score-panel"> <Scorear /> </div>}
            </div>
          </div>
        </div>
      </main>

      {/* Drawer / Off-canvas for Redes Detectadas */}
      <div className={`drawer ${openRedes ? 'open' : ''}`} role="dialog" aria-hidden={!openRedes}>
        <div className="drawer-inner">
          <div className="drawer-header">
            <div className="drawer-title">Redes Detectadas</div>
            <button className="x" onClick={() => setOpenRedes(false)}>×</button>
          </div>
          <div className="drawer-body"><Redes /></div>
        </div>
        <div className="drawer-backdrop" onClick={() => setOpenRedes(false)} />
      </div>
    </div>
  )
}
