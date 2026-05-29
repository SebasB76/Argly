// En dev usa el proxy de Vite (/api). En producción (Vercel) se define
// VITE_API_BASE con la URL del backend, p. ej. https://argly-api.onrender.com/api
const BASE = import.meta.env.VITE_API_BASE || '/api'
export const API_BASE = BASE

// URLs directas para abrir/descargar (GET sin fetch)
export const URL_REPORTE_PDF = `${BASE}/reporte/pdf`
export const URL_REPORTE_EXCEL = `${BASE}/reporte/excel`

export async function getResumen() {
  const r = await fetch(`${BASE}/resumen`)
  return r.json()
}

// filtros: { nivel, estado, ramo, ciudad, proveedor, motivo, q, monto_min, monto_max, score_min, score_max, orden, limit }
export async function getCasos(filtros = {}) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(filtros)) {
    if (v === '' || v == null) continue
    if (k === 'nivel' && v === 'TODOS') continue
    q.set(k, v)
  }
  if (!q.has('limit')) q.set('limit', 200)
  const r = await fetch(`${BASE}/casos?${q}`)
  return r.json()
}

export async function setEstado(id, estado) {
  const r = await fetch(`${BASE}/casos/${id}/estado`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ estado }),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || 'Error al cambiar estado')
  return data
}

export async function getCaso(id) {
  const r = await fetch(`${BASE}/casos/${id}`)
  return r.json()
}

export async function preguntar(pregunta) {
  const r = await fetch(`${BASE}/preguntar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pregunta }),
  })
  return r.json()
}

export async function scorear(caso) {
  const r = await fetch(`${BASE}/scorear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(caso),
  })
  return r.json()
}

export async function getRedes() {
  const r = await fetch(`${BASE}/redes`)
  return r.json()
}

export async function getAhorro() {
  const r = await fetch(`${BASE}/ahorro`)
  return r.json()
}

export async function getProveedoresPareto(objetivo = 0.8) {
  const r = await fetch(`${BASE}/proveedores-pareto?objetivo=${objetivo}`)
  return r.json()
}

export async function getImportancias() {
  const r = await fetch(`${BASE}/modelo/importancias`)
  return r.json()
}

export async function getDataset() {
  const r = await fetch(`${BASE}/dataset`)
  return r.json()
}

// archivos: { siniestros: File, polizas: File, ... } (solo las tablas que se suban)
export async function importarDataset(archivos, modo = 'replace') {
  const fd = new FormData()
  fd.append('modo', modo)
  for (const [tabla, file] of Object.entries(archivos)) {
    if (file) fd.append(tabla, file, file.name)
  }
  const r = await fetch(`${BASE}/dataset/importar`, { method: 'POST', body: fd })
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || 'Error al importar')
  return data
}

export async function resetDataset() {
  const r = await fetch(`${BASE}/dataset/reset`, { method: 'POST' })
  return r.json()
}

export async function enviarFeedback(id, veredicto, nota = '') {
  const r = await fetch(`${BASE}/casos/${id}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ veredicto, nota }),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || 'Error al enviar feedback')
  return data
}

export async function getFeedback() {
  const r = await fetch(`${BASE}/feedback`)
  return r.json()
}

export async function reentrenar() {
  const r = await fetch(`${BASE}/modelo/reentrenar`, { method: 'POST' })
  return r.json()
}

export async function getSesgo() {
  const r = await fetch(`${BASE}/sesgo`)
  return r.json()
}

export async function getContrafactual(id) {
  const r = await fetch(`${BASE}/casos/${id}/contrafactual`)
  return r.json()
}

export async function getMapa() {
  const r = await fetch(`${BASE}/mapa`)
  return r.json()
}

export async function getVinculos(id) {
  const r = await fetch(`${BASE}/casos/${id}/vinculos`)
  return r.json()
}

export async function getBitacora(id) {
  const r = await fetch(`${BASE}/casos/${id}/bitacora`)
  return r.json()
}

export async function agregarNota(id, texto) {
  const r = await fetch(`${BASE}/casos/${id}/nota`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto }),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || 'Error al guardar la nota')
  return data
}

export async function getChecklist(id) {
  const r = await fetch(`${BASE}/casos/${id}/checklist`)
  return r.json()
}

export async function setChecklistPaso(id, clave, hecho) {
  const r = await fetch(`${BASE}/casos/${id}/checklist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clave, hecho }),
  })
  return r.json()
}

export async function getMiTrabajo() {
  const r = await fetch(`${BASE}/mi-trabajo`)
  return r.json()
}
