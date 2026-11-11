import { useEffect, useRef, useState } from 'react'
import { calculateQuote } from './commercialQuote.js'
import { buildProductionLayoutRequest, DEMO_COMPANY_ID, selectedProfileColor } from './productionOrderRequest.js'
import './full-quote.css'

const company = import.meta.env.VITE_COMPANY_ID || DEMO_COMPANY_ID

function PdfActions({ payload, apiUrl, number }) {
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const active = useRef(null)
  useEffect(() => () => active.current?.abort(), [])
  useEffect(() => () => { if (result) URL.revokeObjectURL(result.url) }, [result])

  async function generate() {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const response = await fetch(apiUrl + '/api/v1/quotes/full-pdf', {
        method: 'POST', signal: controller.signal, headers: { 'Content-Type': 'application/json' }, body: payload,
      })
      if (!response.ok) {
        const detail = (await response.json().catch(() => ({}))).detail
        throw new Error(typeof detail === 'string' ? detail : 'Revise os dados do pedido e a conexão com a API.')
      }
      if (!response.headers.get('Content-Type')?.includes('application/pdf')) throw new Error('A API não retornou um PDF.')
      const blob = await response.blob()
      if (!controller.signal.aborted) setResult({ url: URL.createObjectURL(blob), missing: response.headers.get('X-Quote-Missing-Sketches') })
    } catch (err) {
      if (!controller.signal.aborted) setError(err.message)
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }
  return <>
    <button className="primary" onClick={generate} disabled={busy || !payload}>{busy ? 'Gerando PDF…' : 'Gerar PDF do orçamento'}</button>
    {error && <p role="alert" className="op-error">{error}</p>}
    {result && <div className="op-result" role="status"><strong>PDF gerado</strong>
      {result.missing && <p>Croqui indisponível nos itens {result.missing}. A ausência está indicada no documento.</p>}
      <div className="op-file-actions"><a className="secondary" href={result.url} target="_blank" rel="noreferrer">Visualizar PDF</a>
      <a className="primary" href={result.url} download={'Orcamento-' + (number || 'completo').replace(/[^\w.-]/g, '-') + '.pdf'}>Baixar PDF</a></div>
    </div>}
  </>
}

export default function FullQuoteDialog({ quote, setQuote, items, data, apiUrl, close, money }) {
  const dialog = useRef(null)
  useEffect(() => {
    const node = dialog.current
    node.showModal()
    return () => node.close()
  }, [])
  const result = calculateQuote(items, data?.items, quote.commercial)
  const options = quote.fullPdf || {}
  const update = (key, value) => setQuote(old => ({ ...old, fullPdf: { ...old.fullPdf, [key]: value } }))
  const colors = options.colors || {}
  let payload = null
  let message = ''
  if (!result) message = 'Recalcule o pedido para gerar o documento com os valores atuais.'
  else {
    try {
      const metadata = Object.fromEntries(items.map(item => [item.id, { finishKey: colors[item.id] || item.finish_key }]))
      const request = buildProductionLayoutRequest(items, quote, items.map(item => item.id), metadata, company)
      payload = JSON.stringify({
        company_id: company, client: quote.client, number: quote.number, city: quote.city, phone: quote.phone,
        project: quote.project, client_code: quote.clientCode || '', work_code: quote.workCode || '',
        date: (quote.date || '').split('-').reverse().join('/'), notes: quote.notes,
        payment: options.payment || '', delivery: options.delivery || '', validity: options.validity || '',
        installation: result.installation, lines: request.production_order.items.map((entry, i) => ({
          technical: entry.technical_input, label: request.context.item_labels[i].label, finish: entry.finish_key,
          unit: result.rows[i].unit, total: result.rows[i].total,
        })),
      })
    } catch (err) { message = err.message }
  }
  return <dialog ref={dialog} className="full-quote-dialog" aria-labelledby="quote-pdf-title" onCancel={close}>
    <div className="modal-head"><div><strong id="quote-pdf-title">Orçamento completo em PDF</strong>
      <span>{quote.client} · {quote.number}</span></div><button autoFocus onClick={close} aria-label="Fechar">×</button></div>
    <div className="full-quote-body">
      <div className="form-grid">{[['payment', 'Condições de pagamento'], ['delivery', 'Prazo de entrega'], ['validity', 'Validade']].map(([key, label]) =>
        <label key={key}>{label}<input maxLength={500} value={options[key] || ''} onChange={e => update(key, e.target.value)} /></label>)}</div>
      <div className="table-scroll"><table><thead><tr><th>Item</th><th>Medidas (mm)</th><th>Qtd.</th><th>Cor do croqui</th><th>Total</th></tr></thead>
        <tbody>{items.map((item, i) => <tr key={item.id}><td>{i + 1} · {item.family || 'CR'}</td><td>{item.width_mm} × {item.height_mm}</td><td>{item.quantity}</td>
          <td><select aria-label={'Cor do croqui do item ' + (i + 1)} value={selectedProfileColor(colors[item.id] || item.finish_key)}
            onChange={e => update('colors', { ...colors, [item.id]: e.target.value })}><option value="BRANCO">Branco</option><option value="PRETO">Preto</option></select></td>
          <td>{result ? money(result.rows[i].total) : '—'}</td></tr>)}</tbody></table></div>
      {result && <div className="summary-line"><span>Total com instalação</span><strong>{money(result.total)}</strong></div>}
      {message && <p role="status">{message}</p>}
      <PdfActions key={payload || 'empty'} payload={payload} apiUrl={apiUrl} number={quote.number} />
    </div>
  </dialog>
}
