// Extracts the human-visible answer from whatever shape the LLM endpoint returns
// (raw string, fenced JSON, {respuesta}, OpenAI/Gemini-style candidates/choices, etc.)
export function extraerRespuestaVisible(valor) {
  if (valor == null) return ''

  if (typeof valor === 'object') {
    if (typeof valor.respuesta === 'string' && valor.respuesta.trim()) {
      return extraerRespuestaVisible(valor.respuesta)
    }
    if (Array.isArray(valor.candidates) && valor.candidates.length > 0) {
      return extraerRespuestaVisible(valor.candidates[0])
    }
    if (Array.isArray(valor.choices) && valor.choices.length > 0) {
      return extraerRespuestaVisible(valor.choices[0])
    }
    if (valor.content) {
      return extraerRespuestaVisible(valor.content)
    }
    if (Array.isArray(valor.parts) && valor.parts.length > 0) {
      const parte = valor.parts.find((p) => p && typeof p === 'object' && (p.text || p.content))
      if (parte) return extraerRespuestaVisible(parte)
    }
    return extraerRespuestaVisible(valor.text ?? valor.content ?? '')
  }

  const texto = String(valor).trim()
  if (!texto) return ''

  const sinFences = texto
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```\s*$/i, '')
    .trim()

  const limpiado = sinFences.replace(/^json\s*/i, '').trim()

  for (let i = 0; i < 2; i += 1) {
    try {
      const parsed = JSON.parse(limpiado)
      if (typeof parsed === 'string') {
        return extraerRespuestaVisible(parsed)
      }
      if (parsed && typeof parsed === 'object') {
        const respuesta = parsed.respuesta ?? parsed.text ?? parsed.content ?? parsed.message?.content?.text
        if (typeof respuesta === 'string' && respuesta.trim()) {
          return extraerRespuestaVisible(respuesta)
        }
        if (Array.isArray(parsed.candidates) && parsed.candidates.length > 0) {
          return extraerRespuestaVisible(parsed.candidates[0])
        }
        if (Array.isArray(parsed.choices) && parsed.choices.length > 0) {
          return extraerRespuestaVisible(parsed.choices[0])
        }
        return ''
      }
    } catch {
      break
    }
  }

  const coincidenciaRespuesta = limpiado.match(/"respuesta"\s*:\s*"([\s\S]*?)"(?:\s*,|\s*})/i)
  if (coincidenciaRespuesta?.[1]) {
    return coincidenciaRespuesta[1].replace(/\\"/g, '"').trim()
  }

  return limpiado
}
