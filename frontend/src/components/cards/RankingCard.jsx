import { Fragment, useState } from 'react'
import CasoCard from './CasoCard'
import { seedFromItem } from '../../lib/widgets'

export default function RankingCard({ items }) {
  const [first, ...rest] = items
  const [openId, setOpenId] = useState(null)
  if (!first) return null

  return (
    <div className="rankcard">
      <CasoCard id={first.id_siniestro} seed={seedFromItem(first)} autoload />
      {rest.length > 0 && (
        <div className="rank-chips">
          {rest.map((it) => (
            <Fragment key={it.id_siniestro}>
              <button
                className={`rank-chip ${String(it.nivel).toLowerCase()} ${openId === it.id_siniestro ? 'on' : ''}`}
                onClick={() => setOpenId((o) => (o === it.id_siniestro ? null : it.id_siniestro))}
              >
                <span className="badge">{it.score}</span>
                <span className="mono rc-id">{it.id_siniestro}</span>
                <span className="rc-motivo">{it.motivo || it.motivo_principal || ''}</span>
                <span className="rc-caret">{openId === it.id_siniestro ? '▾' : '▸'}</span>
              </button>
              {openId === it.id_siniestro && <CasoCard id={it.id_siniestro} seed={seedFromItem(it)} autoload />}
            </Fragment>
          ))}
        </div>
      )}
    </div>
  )
}
