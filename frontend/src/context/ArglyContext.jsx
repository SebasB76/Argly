import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { getCaso } from '../api'

const Ctx = createContext(null)

export function ArglyProvider({ children }) {
  const [vista, setVista] = useState('overview')
  const [casoSel, setCasoSel] = useState(null) // id pendiente de abrir en la vista Casos
  const cache = useRef(new Map())               // id -> Promise<dossier> (dedup + persistencia en memoria)

  // Abre un caso en la vista Casos (desde una tarjeta del chat)
  const abrirCaso = useCallback((id) => { setCasoSel(id); setVista('casos') }, [])

  // Fetch del dossier completo con cache de promesas (evita refetch y dobles llamadas)
  const fetchCaso = useCallback((id) => {
    if (cache.current.has(id)) return cache.current.get(id)
    const p = getCaso(id).catch((e) => { cache.current.delete(id); throw e })
    cache.current.set(id, p)
    return p
  }, [])

  // Invalida la cache de un caso (p. ej. tras registrar feedback del analista)
  const invalidarCaso = useCallback((id) => { cache.current.delete(id) }, [])

  return (
    <Ctx.Provider value={{ vista, setVista, casoSel, setCasoSel, abrirCaso, fetchCaso, invalidarCaso }}>
      {children}
    </Ctx.Provider>
  )
}

export function useArgly() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useArgly debe usarse dentro de <ArglyProvider>')
  return ctx
}
