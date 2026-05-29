import { useEffect, useRef, useState } from 'react'
import { preguntar } from '../api'
import { extraerRespuestaVisible } from '../lib/respuesta'
import MessageWidgets from './cards/MessageWidgets'

const CHIPS = [
  { label: 'Caso más grave', q: '¿Cuál es el caso más grave de toda la bandeja?' },
  { label: 'Top 5 ROJO', q: 'Dame el top 5 de siniestros ROJO para revisar primero.' },
  { label: 'Anillos', q: '¿Qué anillos o redes de proveedores detectaste?' },
  { label: 'Resumen', q: 'Dame un resumen ejecutivo de la bandeja.' },
  { label: 'Ahorro', q: '¿Cuál es el ahorro potencial estimado?' },
]
const KEY = 'argly.chat.v1'

const hora = (ts) => { try { return new Date(ts).toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit', hour12: false }) } catch { return '' } }

export default function Asistente() {
  const [messages, setMessages] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY)) || [] } catch { return [] }
  })
  const [q, setQ] = useState('')
  const [cargando, setCargando] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify(messages)) } catch { /* quota */ } }, [messages])
  useEffect(() => { const el = scrollRef.current; if (el) el.scrollTop = el.scrollHeight }, [messages, cargando])

  const enviar = async (texto) => {
    const pregunta = (texto ?? q).trim()
    if (!pregunta || cargando) return
    setQ('')
    setMessages((m) => [...m, { role: 'user', text: pregunta, ts: Date.now() }])
    setCargando(true)
    try {
      const r = await preguntar(pregunta)
      const text = extraerRespuestaVisible(r?.respuesta) || extraerRespuestaVisible(r) || 'Sin respuesta del agente.'
      setMessages((m) => [...m, { role: 'assistant', text, ts: Date.now(), error: !!r?.error, herramienta: r?.herramienta, datos: r?.datos }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', text: 'No pude consultar al agente. ¿Está corriendo la API?', ts: Date.now(), error: true }])
    } finally {
      setCargando(false)
    }
  }

  const empty = messages.length === 0

  return (
    <div className="asistente">
      <div className="chat-head">
        <div className="chat-title"><span className="dot" /> ARGLY · Asistente</div>
        <div className="chat-actions">
          <span className="chat-meta">{messages.length} mensajes · persistente</span>
          <button className="chat-clear" onClick={() => setMessages([])} disabled={empty}>Limpiar</button>
        </div>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {empty && (
          <div className="chat-empty">
            <div className="ce-mark">✦</div>
            <div className="ce-title">Pregúntale a ARGLY sobre la bandeja</div>
            <div className="ce-sub">Te responde con tarjetas vivas — dossiers, rankings y anillos — ancladas a datos reales. Prueba:</div>
            <div className="ce-sugs">
              {CHIPS.map((c) => <button key={c.label} onClick={() => enviar(c.q)}>{c.label}</button>)}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role} ${m.error ? 'err' : ''}`}>
            <div className="msg-avatar">{m.role === 'user' ? 'TÚ' : '◎'}</div>
            <div className="msg-col">
              <div className="msg-body">{m.text}</div>
              {m.role === 'assistant' && !m.error && <MessageWidgets msg={m} />}
              <div className="msg-ts">{hora(m.ts)}</div>
            </div>
          </div>
        ))}

        {cargando && (
          <div className="msg assistant">
            <div className="msg-avatar">◎</div>
            <div className="msg-col">
              <div className="msg-body typing"><i /><i /><i /></div>
            </div>
          </div>
        )}
      </div>

      {!empty && (
        <div className="chat-chips">
          {CHIPS.map((c) => <button key={c.label} onClick={() => enviar(c.q)} disabled={cargando}>{c.label}</button>)}
        </div>
      )}

      <div className="chat-input">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && enviar()}
          placeholder="Escribe tu consulta a ARGLY…"
        />
        <button onClick={() => enviar()} disabled={cargando || !q.trim()}>{cargando ? 'TX···' : 'Enviar ↵'}</button>
      </div>
    </div>
  )
}
