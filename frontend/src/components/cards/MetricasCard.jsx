import { Segmented } from '../charts'
import { fmtMoney, fmtNum, fmtPct } from '../../lib/format'

export default function MetricasCard({ herramienta, datos = {} }) {
  if (herramienta === 'simulacion_ahorro') {
    return (
      <div className="chatwidget">
        <div className="cw-head">Ahorro potencial estimado</div>
        <Segmented
          total={fmtMoney(datos.ahorro_estimado_total)}
          totalLabel="ahorro total"
          segments={[
            { label: 'Fraude evitado', value: datos.ahorro_por_fraude_evitado, color: 'var(--verde)', display: fmtMoney(datos.ahorro_por_fraude_evitado) },
            { label: 'Eficiencia operativa', value: datos.ahorro_operativo_priorizacion, color: 'var(--phos)', display: fmtMoney(datos.ahorro_operativo_priorizacion) },
          ]}
        />
        {datos.supuestos && <div className="cw-cap">{datos.supuestos}</div>}
      </div>
    )
  }

  if (herramienta === 'resumen_ejecutivo') {
    const tiles = [
      { b: fmtNum(datos.total), s: 'Total' },
      { b: fmtNum(datos.rojo), s: 'Rojo', c: 'r' },
      { b: fmtNum(datos.amarillo), s: 'Amarillo', c: 'a' },
      { b: fmtMoney(datos.monto_en_revision), s: 'En revisión' },
    ]
    return (
      <div className="chatwidget">
        <div className="cw-head">Resumen ejecutivo</div>
        <div className="cw-tiles">
          {tiles.map((t, i) => <div className="cw-tile" key={i}><b className={t.c || ''}>{t.b}</b><span>{t.s}</span></div>)}
        </div>
        {datos.patron_top && <div className="cw-cap">Patrón dominante: {datos.patron_top.patron} ({datos.patron_top.casos} casos)</div>}
      </div>
    )
  }

  // resumen_ml u otros: tiles genéricos con lo que exista
  const tiles = [
    datos.riesgo_promedio_ml != null && { b: fmtPct(datos.riesgo_promedio_ml * 100), s: 'Riesgo ML prom.' },
    datos.rareza_promedio != null && { b: fmtPct(datos.rareza_promedio * 100), s: 'Rareza prom.' },
    datos.total != null && { b: fmtNum(datos.total), s: 'Total' },
  ].filter(Boolean)
  return (
    <div className="chatwidget">
      <div className="cw-head">Modelo ML</div>
      <div className="cw-tiles">
        {tiles.map((t, i) => <div className="cw-tile" key={i}><b>{t.b}</b><span>{t.s}</span></div>)}
      </div>
    </div>
  )
}
