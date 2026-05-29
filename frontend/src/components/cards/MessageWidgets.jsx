import { widgetFor, asList, extractCaseIds, seedFromItem } from '../../lib/widgets'
import CasoCard from './CasoCard'
import RankingCard from './RankingCard'
import RedCard from './RedCard'
import MetricasCard from './MetricasCard'

// Decide qué tarjeta(s) pintar bajo el texto de un mensaje del asistente.
export default function MessageWidgets({ msg }) {
  const w = widgetFor(msg.herramienta)

  if (w === 'caso' && msg.datos?.id_siniestro) {
    return <CasoCard id={msg.datos.id_siniestro} seed={seedFromItem(msg.datos)} autoload />
  }
  if (w === 'ranking') {
    const items = asList(msg.datos).filter((it) => it?.id_siniestro)
    if (items.length) return <RankingCard items={items} />
  }
  if (w === 'red') return <RedCard herramienta={msg.herramienta} datos={msg.datos} />
  if (w === 'metricas') return <MetricasCard herramienta={msg.herramienta} datos={msg.datos} />

  // Fallback: si el texto menciona ids de siniestro, pinta sus tarjetas igual.
  const ids = extractCaseIds(msg.text)
  if (ids.length) return <div className="cck-stack">{ids.slice(0, 3).map((id) => <CasoCard key={id} id={id} autoload />)}</div>

  return null
}
