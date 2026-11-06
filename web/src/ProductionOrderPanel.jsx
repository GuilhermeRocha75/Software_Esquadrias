import { useEffect, useRef, useState } from 'react'
import { generateProductionOrderReview } from './productionOrderPdf.js'
import { buildProductionLayoutRequest, DEMO_COMPANY_ID, explainProductionBlocker } from './productionOrderRequest.js'
import './production-order.css'

const COMPANY_ID = import.meta.env.VITE_COMPANY_ID || DEMO_COMPANY_ID

function readMetadata(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '{}')
    if (!value || typeof value !== 'object' || Array.isArray(value)) return {}
    return Object.fromEntries(Object.entries(value).filter(([, entry]) => entry && typeof entry === 'object')
      .map(([id, entry]) => [id, { label: typeof entry.label === 'string' ? entry.label : '',
        finishKey: typeof entry.finishKey === 'string' ? entry.finishKey : '' }]))
  } catch { return {} }
}

export default function ProductionOrderPanel({ items, quote, apiUrl, apiOnline, editing }) {
  const storageKey = `software-esquadrias-op-items:${COMPANY_ID}`
  const [metadata, setMetadata] = useState(() => readMetadata(storageKey))
  const [excluded, setExcluded] = useState([])
  const [job, setJob] = useState(null)
  const [hadAttempt, setHadAttempt] = useState(false)
  const [link, setLink] = useState(null)
  const active = useRef(null)
  const selected = items.filter((item) => !excluded.includes(item.id)).map((item) => item.id)
  const revision = JSON.stringify([items, quote, metadata, selected, editing, apiUrl])
  const currentRevision = useRef(revision)
  currentRevision.current = revision
  const current = job?.revision === revision ? job : null
  const busy = current?.phase === 'CHECKING' || current?.phase === 'GENERATING'
  const currentLink = current?.result && link?.revision === revision ? link : null

  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify(metadata)) } catch { /* OP remains usable without local persistence. */ }
  }, [metadata, storageKey])

  useEffect(() => {
    active.current?.abort()
    setJob(null)
    // Also runs on unmount. Revision guards hide old links before this cleanup.
    return () => active.current?.abort()
  }, [revision])

  useEffect(() => {
    if (!current?.result) return
    const url = URL.createObjectURL(current.result.blob)
    setLink({ url, revision })
    return () => URL.revokeObjectURL(url)
  }, [current?.result, revision])

  const setItemMetadata = (id, key, value) => setMetadata((previous) => ({
    ...previous, [id]: { ...previous[id], [key]: value },
  }))

  const generate = async () => {
    setHadAttempt(true)
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    const isCurrent = () => !controller.signal.aborted && currentRevision.current === revision && active.current === controller
    setJob({ revision, phase: 'CHECKING' })
    try {
      const request = buildProductionLayoutRequest(items, quote, selected, metadata, COMPANY_ID)
      const result = await generateProductionOrderReview(apiUrl, request, {
        signal: controller.signal,
        onReadiness: (readiness) => {
          if (isCurrent()) setJob({ revision, phase: 'GENERATING', readiness })
        },
      })
      if (isCurrent()) setJob({ revision, phase: 'READY', result, readiness: result.readiness })
    } catch (error) {
      if (isCurrent()) setJob((previous) => ({ ...previous, revision, phase: 'ERROR', error: error.message }))
    }
  }

  const cancel = () => {
    active.current?.abort()
    setJob({ revision, phase: 'CANCELLED' })
  }

  const labelFor = (id) => metadata[id]?.label?.trim() || String(items.findIndex((item) => item.id === id) + 1).padStart(2, '0')

  return <section className="card op-card" aria-labelledby="op-title">
    <div className="section-head op-head">
      <div><h2 id="op-title" className="section-title">Ordem de Produção de Conferência</h2>
        <p>Use os itens cadastrados para comparar com o Excel. Fabricação bloqueada.</p></div>
      <button className="primary" onClick={generate} disabled={busy || editing || apiOnline === false || !selected.length}>
        {busy ? (current.phase === 'CHECKING' ? 'Consultando pendências…' : 'Gerando PDF…') : 'Gerar OP de Conferência'}
      </button>
    </div>
    <div className="op-body">
      <p className="op-review-mark">CONFERÊNCIA — NÃO FABRICAR</p>
      <p className="op-help">Selecione um ou vários itens. Identificação e cor do croqui não alteram os cálculos. A cor é a da esquadria, não o arremate interno ou externo; deixe vazia se ainda não souber.</p>
      <div className="op-selection-actions">
        <span>{selected.length} de {items.length} itens selecionados</span>
        <button className="secondary" onClick={() => setExcluded([])} disabled={!items.length}>Selecionar todos</button>
        <button className="secondary" onClick={() => setExcluded(items.map((item) => item.id))} disabled={!items.length}>Limpar seleção</button>
      </div>
      <fieldset className="op-items"><legend>Itens da OP</legend>
        {!items.length && <p>Cadastre uma esquadria na lista acima para gerar a OP.</p>}
        {items.map((item, index) => {
          const ordinal = String(index + 1).padStart(2, '0')
          return <div className="op-item" key={item.id}>
            <label className="op-check"><input type="checkbox" checked={selected.includes(item.id)}
              onChange={(event) => setExcluded((previous) => event.target.checked ? previous.filter((id) => id !== item.id) : [...previous, item.id])} />
              Incluir item {ordinal} ({item.family || 'CR'})</label>
            <label>Identificação do item {ordinal}<input maxLength="100" value={metadata[item.id]?.label ?? ''}
              placeholder={ordinal} onChange={(event) => setItemMetadata(item.id, 'label', event.target.value)} /></label>
            <label>Cor do croqui do item {ordinal}<input list="op-colors" maxLength="100" value={metadata[item.id]?.finishKey ?? item.finish_key ?? ''}
              placeholder="Não informada" onChange={(event) => setItemMetadata(item.id, 'finishKey', event.target.value)} /></label>
          </div>
        })}
      </fieldset>
      <datalist id="op-colors"><option value="BRANCO" /><option value="PRETO" /></datalist>
      {apiOnline === false && <p className="op-error" role="alert">API indisponível. Ligue o servidor para gerar a OP de conferência.</p>}
      {editing && <p>Salve ou cancele a edição da esquadria antes de gerar a OP.</p>}
      {busy && <div className="op-progress" aria-live="polite"><p>{current.phase === 'CHECKING' ? 'Consultando os dados e as pendências da OP…' : 'Gerando o PDF de conferência com as pendências abaixo…'}</p><button className="secondary" onClick={cancel}>Cancelar geração</button></div>}
      {current?.phase === 'CANCELLED' && <p aria-live="polite">Geração cancelada. Nenhum novo PDF foi disponibilizado.</p>}
      {current?.error && <p className="op-error" role="alert">{current.error}</p>}
      {current?.readiness && <div className="op-findings" aria-live="polite">
        <h3>Pendências da OP ({current.readiness.blockers.length})</h3>
        <p>Estas pendências impedem a liberação para fabricação. A conferência pode ser visualizada.</p>
        <ul>{current.readiness.blockers.map((blocker, index) => <li key={`${blocker.code}-${index}`}>
          <strong>{blocker.item_id ? `Item ${labelFor(blocker.item_id)}` : 'Pedido'}{blocker.engine_position != null ? `, linha ${blocker.engine_position}` : ''}: </strong>
          {explainProductionBlocker(blocker)}
          <details><summary>Detalhe técnico: {blocker.code}</summary><p>{blocker.message}</p></details>
        </li>)}</ul>
      </div>}
      {currentLink && <div className="op-result">
        <p aria-live="polite">PDF de conferência gerado: {current.result.pages} páginas. Revise todas as pendências antes de comparar com o Excel.</p>
        <div className="op-file-actions">
          <a className="secondary" href={currentLink.url} target="_blank" rel="noopener noreferrer">Abrir PDF de conferência</a>
          <a className="primary" href={currentLink.url} download={current.result.filename}>Salvar PDF de conferência</a>
        </div>
        <iframe title="Prévia da OP de conferência" src={currentLink.url} />
      </div>}
      {!current && hadAttempt && <p aria-live="polite">O pedido ou a seleção mudou. Gere novamente para conferir os dados atuais.</p>}
    </div>
  </section>
}
