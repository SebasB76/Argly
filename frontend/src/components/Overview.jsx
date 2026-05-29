import { useEffect, useState } from 'react'
import { getProveedoresPareto, getImportancias, getAhorro, getCasos, getMapa } from '../api'
import { ChartCard, Donut, ParetoChart, BarsH, Segmented, Histogram } from './charts'
import MapaCalor from './MapaCalor'
import Stats from './Stats'
import { fmtMoney, fmtMoneyK, fmtNum, fmtPct, humanize } from '../lib/format'

export default function Overview({ resumen }) {
  const [pareto, setPareto] = useState(null)
  const [imp, setImp] = useState(null)
  const [ahorro, setAhorro] = useState(null)
  const [scores, setScores] = useState([])
  const [mapa, setMapa] = useState(null)

  useEffect(() => {
    getProveedoresPareto(0.8).then(setPareto).catch(() => {})
    getImportancias().then(setImp).catch(() => {})
    getAhorro().then(setAhorro).catch(() => {})
    getCasos({ limit: 2000 }).then((d) => setScores((d.casos || []).map((c) => c.score))).catch(() => {})
    getMapa().then(setMapa).catch(() => {})
  }, [])

  const n = resumen?.por_nivel || {}
  const donutSegs = [
    { label: 'Rojo', value: n.ROJO || 0, color: 'var(--rojo)' },
    { label: 'Amarillo', value: n.AMARILLO || 0, color: 'var(--amar)' },
    { label: 'Verde', value: n.VERDE || 0, color: 'var(--verde)' },
  ]
  const paretoItems = (pareto?.proveedores || []).map((p) => ({ label: p.id_proveedor, value: p.alertas, cum: p.pct_acumulado }))
  const impItems = Object.entries(imp?.importancias || {})
    .map(([k, v]) => ({ label: humanize(k), value: v }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="overview">
      <Stats resumen={resumen} />

      {/* --- 1. Panorama: cómo se distribuye el riesgo --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Panorama</span>
          <h3>Distribución del riesgo</h3>
        </div>
        <div className="overview-grid">
          <ChartCard eyebrow="Semáforo de riesgo" title="Distribución de siniestros" sub="Triage automático por nivel">
            {resumen
              ? <Donut segments={donutSegs} centerValue={fmtNum(resumen.total)} centerLabel="siniestros" />
              : <div className="cc-loading">Cargando…</div>}
          </ChartCard>

          <ChartCard span="span2" eyebrow="Calibración" title="Distribución del score (0–100)" sub={`${fmtNum(scores.length)} siniestros · verde → amarillo → rojo`}>
            {scores.length
              ? <Histogram scores={scores} bins={10} />
              : <div className="cc-loading">Cargando…</div>}
          </ChartCard>
        </div>
      </section>

      {/* --- 2. Focos de fraude: dónde se concentra --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Focos de fraude</span>
          <h3>Dónde se concentra</h3>
        </div>
        <div className="overview-grid">
          <ChartCard
            span="span3"
            eyebrow="Distribución geográfica"
            title="Mapa de calor · alertas por ciudad"
            sub="¿Qué ciudades concentran más alertas? (datos georreferenciados, sin APIs externas)"
            right={mapa && <span className="cc-badge">{mapa.con_coordenadas} ciudades</span>}
          >
            <MapaCalor data={mapa} />
          </ChartCard>

          <ChartCard
            span="span3"
            eyebrow="Concentración de fraude"
            title="Pareto 80/20 · proveedores con alertas rojas"
            sub={pareto?.interpretacion}
            right={pareto && <span className="cc-badge">{pareto.n_proveedores_concentran}/{pareto.total_proveedores_con_alertas} concentran {pareto.objetivo_pct}%</span>}
          >
            {paretoItems.length
              ? <ParetoChart items={paretoItems} target={pareto?.objetivo_pct || 80} />
              : <div className="cc-loading">Cargando…</div>}
          </ChartCard>
        </div>
      </section>

      {/* --- 3. Modelo e impacto: por qué y cuánto --- */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Modelo e impacto</span>
          <h3>Por qué y cuánto</h3>
        </div>
        <div className="overview-grid">
          <ChartCard eyebrow="Explicabilidad (SHAP)" title="Señales que más pesan" sub="Importancia media en el modelo ML">
            {impItems.length
              ? <BarsH items={impItems} max={10} />
              : <div className="cc-loading">Cargando…</div>}
          </ChartCard>

          <ChartCard
            span="span2"
            eyebrow="Impacto económico"
            title="Ahorro potencial estimado"
            sub={ahorro?.supuestos}
            right={ahorro && <span className="cc-badge warn">cifra referencial</span>}
          >
            {ahorro ? (
              <div className="ahorro-wrap">
                <Segmented
                  total={fmtMoney(ahorro.ahorro_estimado_total)}
                  totalLabel="ahorro potencial total"
                  segments={[
                    { label: 'Fraude evitado (35% confirmado)', value: ahorro.ahorro_por_fraude_evitado, color: 'var(--verde)', display: fmtMoney(ahorro.ahorro_por_fraude_evitado) },
                    { label: 'Eficiencia operativa (priorización)', value: ahorro.ahorro_operativo_priorizacion, color: 'var(--phos)', display: fmtMoney(ahorro.ahorro_operativo_priorizacion) },
                  ]}
                />
                <div className="ahorro-tiles">
                  <div className="atile"><b>{fmtMoneyK(ahorro.monto_expuesto_rojo)}</b><span>Monto expuesto (rojo)</span></div>
                  <div className="atile"><b>{fmtNum(ahorro.casos_rojos)}</b><span>Casos rojos</span></div>
                  <div className="atile"><b>{fmtNum(ahorro.casos_en_revision)}</b><span>En revisión</span></div>
                  <div className="atile"><b>{fmtPct(ahorro.tasa_fraude_confirmado_estimada * 100)}</b><span>Tasa confirmada (est.)</span></div>
                </div>
              </div>
            ) : <div className="cc-loading">Cargando…</div>}
          </ChartCard>
        </div>
      </section>
    </div>
  )
}
