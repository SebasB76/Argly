import { useEffect, useState } from 'react'
import { getResumen, getCasos, getCaso } from './api'
import Stats from './components/Stats'
import Bandeja from './components/Bandeja'
import Detalle from './components/Detalle'
import './App.css'

const NIVELES = ['TODOS', 'ROJO', 'AMARILLO', 'VERDE']

export default function App() {
  const [resumen, setResumen] = useState(null)
  const [casos, setCasos] = useState([])
  const [filtro, setFiltro] = useState('TODOS')
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(false)

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
        <div className="aviso">⚠ ALERTA para revisión humana · NO es una acusación de fraude</div>
      </header>

      <Stats resumen={resumen} />

      <div className="filtros">
        {NIVELES.map((n) => (
          <button key={n} className={`f ${filtro === n ? 'on' : ''}`} onClick={() => setFiltro(n)}>{n}</button>
        ))}
      </div>

      <div className="layout">
        <Bandeja casos={casos} cargando={cargando} onSelect={abrir} sel={detalle?.id_siniestro} />
        <Detalle d={detalle} onClose={() => setDetalle(null)} />
      </div>
    </div>
  )
}
