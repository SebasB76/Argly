import { useState } from 'react'
import { scorear } from '../api'

const COBERTURAS = ['Choque', 'Robo', 'Pérdida Total', 'Daño a Terceros (RC)', 'Atención Médica']

const INICIAL = {
  dias_desde_inicio_poliza: 5, cobertura: 'Choque', monto_reclamado: 10000, suma_asegurada: 15000,
  dias_entre_ocurrencia_reporte: 1, historial_siniestros_asegurado: 1,
  documentos_completos: true, proveedor_en_lista: false, clima_inconsistente: false, doc_inconsistente: false,
}
const PRESET_24H = {
  ...INICIAL, dias_desde_inicio_poliza: 1, cobertura: 'Robo',
  dias_entre_ocurrencia_reporte: 6, monto_reclamado: 14500, suma_asegurada: 15000,
}

export default function Scorear() {
  const [f, setF] = useState(INICIAL)
  const [res, setRes] = useState(null)
  const [cargando, setCargando] = useState(false)
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }))

  const enviar = async (caso) => {
    setCargando(true)
    setRes(null)
    try { setRes(await scorear(caso || f)) } catch { setRes({ error: true }) } finally { setCargando(false) }
  }

  return (
    <div className="scorear">
      <div className="scorear-h">Simulador de scoring</div>
      <div className="scorear-grid">
        <label>Días desde inicio de póliza
          <input type="number" value={f.dias_desde_inicio_poliza} onChange={(e) => set('dias_desde_inicio_poliza', +e.target.value)} /></label>
        <label>Cobertura
          <select value={f.cobertura} onChange={(e) => set('cobertura', e.target.value)}>
            {COBERTURAS.map((c) => <option key={c}>{c}</option>)}
          </select></label>
        <label>Días ocurrencia → reporte
          <input type="number" value={f.dias_entre_ocurrencia_reporte} onChange={(e) => set('dias_entre_ocurrencia_reporte', +e.target.value)} /></label>
        <label>Monto reclamado
          <input type="number" value={f.monto_reclamado} onChange={(e) => set('monto_reclamado', +e.target.value)} /></label>
        <label>Suma asegurada
          <input type="number" value={f.suma_asegurada} onChange={(e) => set('suma_asegurada', +e.target.value)} /></label>
        <label>Siniestros previos del asegurado
          <input type="number" value={f.historial_siniestros_asegurado} onChange={(e) => set('historial_siniestros_asegurado', +e.target.value)} /></label>
      </div>
      <div className="scorear-checks">
        <label><input type="checkbox" checked={f.proveedor_en_lista} onChange={(e) => set('proveedor_en_lista', e.target.checked)} /> Proveedor en lista restrictiva</label>
        <label><input type="checkbox" checked={f.doc_inconsistente} onChange={(e) => set('doc_inconsistente', e.target.checked)} /> Documento adulterado</label>
        <label><input type="checkbox" checked={f.clima_inconsistente} onChange={(e) => set('clima_inconsistente', e.target.checked)} /> Clima inconsistente</label>
        <label><input type="checkbox" checked={!f.documentos_completos} onChange={(e) => set('documentos_completos', !e.target.checked)} /> Documentos incompletos</label>
      </div>
      <div className="scorear-btns">
        <button onClick={() => enviar()} disabled={cargando}>{cargando ? '…' : 'Scorear'}</button>
        <button className="preset" onClick={() => { setF(PRESET_24H); enviar(PRESET_24H) }}>Ejemplo: robo a 24h de la póliza</button>
      </div>
      {res && !res.error && (
        <div className="scorear-res">
          <div className={`scoregauge ${res.nivel.toLowerCase()}`}>
            <span className="sg-num">{res.score}</span>
            <span className="sg-cap">SCORE</span>
          </div>
          <div className="scorear-res-body">
            <div className={`nivel ${res.nivel.toLowerCase()}`}>{res.nivel} · {res.recomendacion}</div>
            <ul className="contribs">
              {[...res.contribuciones].sort((a, b) => b.puntos - a.puntos).map((c, i) => (
                <li key={i} className={c.gate ? 'gate' : ''} style={{ animationDelay: `${i * 45}ms` }}>
                  <span className="pts">+{c.puntos}</span>
                  <div><div className="regla">{c.regla}{c.gate ? ' · GATE' : ''}</div><div className="ev">{c.evidencia}</div></div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
