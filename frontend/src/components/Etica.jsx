import { useEffect, useState } from 'react'
import { getSesgo } from '../api'

const ATTR_LABEL = { ciudad: 'Ciudad', segmento: 'Segmento', canal_venta: 'Canal de venta', ramo: 'Ramo' }

function pct(v) {
  return v == null ? '—' : `${(v * 100).toFixed(1)}%`
}

function GrupoBarra({ g, metrica, max }) {
  const v = g[metrica] ?? g.tasa_alerta
  const w = max > 0 ? Math.max(4, (v / max) * 100) : 0
  return (
    <div className="bias-row">
      <span className="bias-g" title={g.grupo}>{g.grupo}</span>
      <div className="bias-bar"><i style={{ width: `${w}%` }} /></div>
      <span className="bias-v">{pct(v)}</span>
      <span className="bias-n" title="Falsos positivos · n del grupo">
        {g.tasa_falsos_positivos != null ? `FP ${pct(g.tasa_falsos_positivos)}` : `n=${g.n}`}
      </span>
    </div>
  )
}

function AtributoCard({ attr, data }) {
  const metrica = data.metrica_disparidad
  const max = Math.max(...data.grupos.map((g) => g[metrica] ?? g.tasa_alerta ?? 0), 0.0001)
  const ver = data.veredicto
  return (
    <div className="chartcard bias-card">
      <div className="cc-head">
        <div>
          <div className="cc-title">{ATTR_LABEL[attr] || attr}</div>
          <div className="cc-sub">Tasa de alerta por grupo · {data.grupos.length} grupos</div>
        </div>
        {ver && (
          <span className={`bias-verdict ${ver}`}>
            {ver === 'equitativo' ? '✓ Equitativo' : '⚠ Revisar'}
            {data.disparidad != null && <i> · ratio {data.disparidad}</i>}
          </span>
        )}
      </div>
      <div className="bias-rows">
        {data.grupos.map((g) => <GrupoBarra key={g.grupo} g={g} metrica={metrica} max={max} />)}
      </div>
      {ver === 'revisar' && (
        <div className="bias-foot">Grupo más alertado: <b>{data.grupo_mas_alertado}</b>. La disparidad cae por debajo de 0.8 (regla 4/5) → conviene revisión humana.</div>
      )}
    </div>
  )
}

export default function Etica() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(false)

  useEffect(() => { getSesgo().then(setData).catch(() => setErr(true)) }, [])

  if (err) return <div className="detalle vacio">No se pudo cargar el análisis de sesgo.</div>
  if (!data) return <div className="detalle vacio">Calculando equidad…</div>

  const attrs = Object.entries(data.atributos)
  const conVeredicto = attrs.filter(([, d]) => d.veredicto)
  const equitativos = conVeredicto.filter(([, d]) => d.veredicto === 'equitativo').length
  const aRevisar = data.atributos_a_revisar.length

  return (
    <div className="etica">
      <div className="sec-head">
        <span className="sec-eyebrow">Explicabilidad y ética</span>
        <h2 className="sec-title">Análisis de equidad</h2>
      </div>

      {/* Contexto: cómo se mide */}
      <div className="bias-explica">
        <p>
          Verificamos que Argly <b>no sobre-alerte sistemáticamente a ningún grupo</b> (ciudad, segmento,
          canal o ramo). Es una salvaguarda de equidad: una alerta para revisión humana, <b>no una
          conclusión de discriminación</b>.
        </p>
        <ul>
          <li><span className="be-key">Tasa de alerta</span> — % de casos marcados (no verdes) en el grupo. Es la <b>barra</b> de cada grupo.</li>
          <li><span className="be-key">Falsos positivos (FP)</span> — % de casos <i>sin</i> fraude que igual se marcaron: el costo ético de equivocarse.</li>
          <li><span className="be-key">Regla 4/5</span> — la tasa más baja entre grupos debe ser ≥ 80% de la más alta (ratio ≥ 0.8). Por debajo se marca <b>“revisar”</b>.</li>
        </ul>
      </div>

      {/* Veredicto general */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Veredicto general</span>
          <h3>{aRevisar === 0 ? 'Sin disparidades relevantes' : `${aRevisar} atributo(s) a revisar`}</h3>
        </div>
        <div className="bias-kpis">
          <div className="rk ok"><b>{equitativos}</b><span>Atributos equitativos</span></div>
          <div className={`rk ${aRevisar ? 'alerta' : ''}`}><b>{aRevisar}</b><span>Atributos a revisar</span></div>
          <div className="rk"><b>{conVeredicto.length}</b><span>Atributos evaluados</span></div>
          <div className="rk"><b>{data.hay_etiquetas ? 'Sí' : 'No'}</b><span>{data.hay_etiquetas ? 'Falsos positivos medibles' : 'Solo tasa de alerta'}</span></div>
        </div>
      </section>

      {/* Equidad por atributo */}
      <section className="ov-section">
        <div className="ov-sec-head">
          <span className="sec-eyebrow">Detalle</span>
          <h3>Equidad por atributo</h3>
        </div>
        <div className="bias-grid">
          {attrs.map(([attr, d]) => <AtributoCard key={attr} attr={attr} data={d} />)}
        </div>
      </section>

      <div className="sello">{data.nota}</div>
    </div>
  )
}
