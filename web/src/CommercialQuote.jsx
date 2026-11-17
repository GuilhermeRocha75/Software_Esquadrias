import React from 'react'
import { calculateQuote } from './commercialQuote.js'

function Numeric({ label, value, change, placeholder }) {
  return <label>{label}<input type="number" step="any" aria-label={label} value={value}
    placeholder={placeholder} onChange={event => change(event.target.value)} /></label>
}

export default function CommercialQuote({ items, data, quote, setQuote, money, modelLabel }) {
  const settings = quote.commercial || {}
  const update = fn => setQuote(old => ({ ...old, commercial: fn(old.commercial || {}) }))
  const set = (key, value) => update(old => ({ ...old, [key]: value }))
  const setLine = (id, key, value) => update(old => ({
    ...old, lines: { ...old.lines, [id]: { ...old.lines?.[id], [key]: value } },
  }))
  const result = calculateQuote(items, data?.items, settings)
  return <section id="orcamento-comercial" className="card">
    <div className="section-title">Orçamento comercial</div>
    <div className="form-grid">
      <Numeric label="Fator de margem geral" value={settings.factor ?? 1} change={value => update(old => ({
        ...old, factor: value, lines: Object.fromEntries(Object.entries(old.lines || {}).map(([id, line]) => [id, { ...line, factor: '' }]))
      }))} />
      <Numeric label="Instalação (R$/m²)" value={settings.perArea ?? 120} change={v => set('perArea', v)} />
      <Numeric label="Instalação (R$/unidade)" value={settings.perUnit ?? 0} change={v => set('perUnit', v)} />
      <Numeric label="Instalação fixa (R$)" value={settings.fixed ?? 300} change={v => set('fixed', v)} />
    </div>
    {result ? <>
      <div className="table-scroll"><table><thead><tr>{['Item', 'Qtd.', 'Custo técnico/un.', 'Custo manual/un.', 'Fator do item', 'Venda/un.', 'Total'].map(h => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>{result.rows.map((row, i) => {
        const item = items[i]
        const line = settings.lines?.[item.id] || {}
        return <tr key={item.id}><td>{i + 1}. {modelLabel(item)}</td><td>{item.quantity}</td><td>{money(data.items[i].unit_technical_cost)}</td>
          <td><Numeric label={'Custo manual do item ' + (i + 1)} placeholder="Automático" value={line.cost ?? ''} change={v => setLine(item.id, 'cost', v)} /></td>
          <td><Numeric label={'Fator do item ' + (i + 1)} placeholder={String(settings.factor || 1)} value={line.factor ?? ''} change={v => setLine(item.id, 'factor', v)} /></td>
          <td>{money(row.unit)}</td><td>{money(row.total)}</td></tr>
      })}</tbody></table></div>
      <div className="summary-line"><span>Esquadrias</span><strong>{money(result.subtotal)}</strong></div>
      <div className="summary-line"><span>Instalação · {result.area.toLocaleString('pt-BR')} m² · {result.quantity} un.</span><strong>{money(result.installation)}</strong></div>
      <div className="sale-price"><span>Total do orçamento</span><strong>{money(result.total)}</strong></div>
    </> : <p>{items.length > 51 ? 'O resumo do Excel comporta 51 linhas de itens.' : 'Adicione um item e recalcule o pedido para visualizar os valores.'}</p>}
  </section>
}
