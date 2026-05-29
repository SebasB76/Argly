// Mapea la herramienta que usó el agente -> tipo de tarjeta a renderizar en el chat.
// El backend ya devuelve { herramienta, datos } en cada respuesta de /preguntar.

export function widgetFor(herramienta) {
  const h = herramienta || ''
  if (h === 'explicar' || h === 'detalle_caso') return 'caso'
  if (['top_riesgo', 'recomendar', 'buscar_casos', 'montos_atipicos', 'documentos_faltantes', 'borde_vigencia'].includes(h)) return 'ranking'
  if (['proveedores_pareto', 'proveedores_top', 'redes'].includes(h)) return 'red'
  if (['simulacion_ahorro', 'resumen_ejecutivo', 'resumen_ml'].includes(h)) return 'metricas'
  return null
}

// Normaliza `datos` a una lista de casos (top_riesgo-shaped)
export function asList(datos) {
  if (Array.isArray(datos)) return datos
  if (datos && Array.isArray(datos.top_ml)) return datos.top_ml
  return []
}

// Fallback robusto: extrae ids de siniestro mencionados en el texto del agente
export function extractCaseIds(text) {
  const ids = String(text || '').toUpperCase().match(/SIN\d{3,}/g) || []
  return [...new Set(ids)]
}

// Semilla mínima para pintar el encabezado de una CasoCard sin esperar al fetch
export function seedFromItem(it = {}) {
  return {
    score: it.score,
    nivel: it.nivel,
    motivo: it.motivo || it.motivo_principal,
    monto: it.monto ?? it.monto_reclamado,
  }
}
