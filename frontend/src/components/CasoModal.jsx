import { useEffect, useState } from 'react'
import { getCaso } from '../api'
import Detalle from './Detalle'

// Popup que muestra el dossier completo de un caso, cerrable (overlay / Esc / ×).
export default function CasoModal({ id, onClose }) {
  const [d, setD] = useState(null)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    if (!id) return
    setD(null); setCargando(true)
    getCaso(id).then(setD).catch(() => {}).finally(() => setCargando(false))
  }, [id])

  useEffect(() => {
    if (!id) return
    const h = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [id, onClose])

  if (!id) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        {cargando && !d && <div className="detalle vacio">Cargando caso…</div>}
        {d && (
          <Detalle
            d={d}
            onClose={onClose}
            onFeedback={(cid, fb) => setD((p) => (p && p.id_siniestro === cid ? { ...p, feedback: fb } : p))}
            onOpen={(nid) => { setCargando(true); getCaso(nid).then(setD).catch(() => {}).finally(() => setCargando(false)) }}
          />
        )}
      </div>
    </div>
  )
}
