import { useEffect, useState } from 'react'
import { getResumen, getDataset } from './api'
import { useArgly } from './context/ArglyContext'
import Overview from './components/Overview'
import Casos from './components/Casos'
import RedesView from './components/RedesView'
import Asistente from './components/Asistente'
import Datos from './components/Datos'
import Etica from './components/Etica'
import MiTrabajo from './components/MiTrabajo'
import './App.css'

const VIEWS = [
  { id: 'overview', label: 'Overview', sub: 'Analítica', glyph: '▦' },
  { id: 'casos', label: 'Casos', sub: 'Bandeja', glyph: '▤' },
  { id: 'trabajo', label: 'Mi trabajo', sub: 'Operación', glyph: '☑' },
  { id: 'redes', label: 'Redes', sub: 'Grafo', glyph: '◈' },
  { id: 'asistente', label: 'Asistente', sub: 'IA', glyph: '✦' },
  { id: 'etica', label: 'Ética', sub: 'Equidad', glyph: '⚖' },
  { id: 'datos', label: 'Datos', sub: 'Dataset', glyph: '▥' },
]
const TITLES = { overview: 'Centro de mando', casos: 'Bandeja operativa', trabajo: 'Mi trabajo', redes: 'Redes de fraude', asistente: 'Asistente IA', etica: 'Explicabilidad y ética', datos: 'Gestión de datos' }

function useClock() {
  const [t, setT] = useState('')
  useEffect(() => {
    const f = () => setT(new Date().toLocaleTimeString('es-EC', { hour12: false }))
    f()
    const id = setInterval(f, 1000)
    return () => clearInterval(id)
  }, [])
  return t
}

export default function App() {
  const { vista, setVista } = useArgly()
  const [resumen, setResumen] = useState(null)
  const [dataset, setDataset] = useState(null)
  const clock = useClock()

  useEffect(() => { getResumen().then(setResumen).catch(() => {}) }, [])
  useEffect(() => { getDataset().then(setDataset).catch(() => {}) }, [vista])

  const n = resumen?.por_nivel || {}

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sb-brand">
          <span className="sb-mark">◆</span>
          <div className="sb-words">
            <div className="sb-name">ARGLY</div>
            <div className="sb-tag">Antifraude</div>
          </div>
        </div>

        <nav className="sb-nav">
          {VIEWS.map((v) => (
            <button key={v.id} className={`sb-item ${vista === v.id ? 'on' : ''}`} onClick={() => setVista(v.id)}>
              <span className="sb-glyph">{v.glyph}</span>
              <span className="sb-label">{v.label}<i>{v.sub}</i></span>
            </button>
          ))}
        </nav>

        <div className="sb-foot">
          <div className="sb-status"><span className="dot" /> Monitoreando</div>
          <div className="sb-ver">v1.0 · {dataset?.origen === 'importado' ? 'dataset importado' : 'datos sintéticos'}</div>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="tb-title">
            <span className="tb-crumb">ARGLY</span>
            <span className="tb-sep">/</span>
            {TITLES[vista]}
          </div>
          <div className="tb-right">
            {resumen && (
              <div className="tb-kpis">
                <span><b className="r">{n.ROJO || 0}</b> rojo</span>
                <span><b className="a">{n.AMARILLO || 0}</b> amarillo</span>
                <span><b>{(resumen.total || 0).toLocaleString('es-EC')}</b> total</span>
              </div>
            )}
            <span className="status-chip live"><i className="dot" /> Live</span>
            <span className="status-chip mono">{clock}</span>
          </div>
        </header>

        <div className="aviso-bar">
          <span className="aviso-tag">Aviso</span>
          Las señales son <b>&nbsp;alertas para revisión humana&nbsp;</b>, no acusaciones. La decisión final es del analista.
        </div>

        <main className="view" key={vista}>
          {vista === 'overview' && <Overview resumen={resumen} />}
          {vista === 'casos' && <Casos />}
          {vista === 'trabajo' && <MiTrabajo />}
          {vista === 'redes' && <RedesView />}
          {vista === 'asistente' && <Asistente />}
          {vista === 'etica' && <Etica />}
          {vista === 'datos' && <Datos />}
        </main>
      </div>
    </div>
  )
}
