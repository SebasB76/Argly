const BASE = '/api'

export async function getResumen() {
  const r = await fetch(`${BASE}/resumen`)
  return r.json()
}

export async function getCasos(nivel, limit = 200) {
  const q = new URLSearchParams({ limit })
  if (nivel) q.set('nivel', nivel)
  const r = await fetch(`${BASE}/casos?${q}`)
  return r.json()
}

export async function getCaso(id) {
  const r = await fetch(`${BASE}/casos/${id}`)
  return r.json()
}
