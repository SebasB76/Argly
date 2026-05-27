import { useState } from 'react'
import { preguntar } from '../api'

const SUGERENCIAS = [
  '¿Qué proveedores concentran las alertas rojas?',
  'Dame un resumen ejecutivo',
  '¿Qué patrones se repiten?',
  'Recomienda qué revisar primero',
]

export default function Agente() {
  const [q, setQ] = useState('')
  const [resp, setResp] = useState(null)
  const [cargando, setCargando] = useState(false)

  const enviar = async (texto) => {
    const pregunta = (texto ?? q).trim()
    if (!pregunta) return
    setCargando(true)
    setResp(null)
    try {
      setResp(await preguntar(pregunta))
    } catch {
      setResp({ respuesta: 'No pude consultar al agente. ¿Está corriendo la API?' })
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="agente">
      <div className="agente-h">🔎 Pregúntale a Argly</div>
      <div className="agente-in">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && enviar()}
          placeholder="Ej: ¿qué proveedores concentran las alertas rojas?"
        />
        <button onClick={() => enviar()} disabled={cargando}>{cargando ? '…' : 'Preguntar'}</button>
      </div>
      <div className="sugerencias">
        {SUGERENCIAS.map((s) => (
          <button key={s} onClick={() => { setQ(s); enviar(s) }}>{s}</button>
        ))}
      </div>
      {resp && (
        <div className="agente-resp">
          <p>{resp.respuesta}</p>
          {resp.fuente && <div className="agente-meta">motor: {resp.herramienta} · fuente: {resp.fuente}</div>}
        </div>
      )}
    </div>
  )
}
