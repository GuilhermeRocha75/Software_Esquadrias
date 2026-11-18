import React from 'react'

export const groups = {
  profiles: ['Perfis principais', '▱'],
  glass: ['Vidros', '◇'],
  hardware: ['Ferragens', '⚙'],
  seals: ['Borrachas e escovas', '≋'],
  screens: ['Telas', '▦'],
  accessories: ['Acessórios', '⊞'],
}

function groupOf(row) {
  if (/TELA/.test(row.category) || row.role?.startsWith('SCREEN')) return 'screens'
  if (/VIDRO/.test(row.category)) return 'glass'
  if (/VEDA|BORRACHA|ESCOVA/.test(row.category)) return 'seals'
  if (/FERRAGEM|FERRAGENS/.test(row.category)) return 'hardware'
  if (/PERFI|BAGUETE|REFORÇO|ACABAMENTO|TRILHO/.test(row.category)) return 'profiles'
  return 'accessories'
}

export function MaterialOrders({group, data, quote, money, number}) {
  const bom = (data?.items || []).flatMap(item => item.bom || [])
  const bars = new Map((data?.purchase_plan?.lines || []).map(line => [line.material_code, line]))
  const rows = new Map()
  for (const row of bom) {
    const bar = bars.get(row.material_code)
    const category = bar && groupOf(row) !== 'screens' ? 'profiles' : groupOf(row)
    if (category !== group) continue
    const area = row.unit === 'm²'
    const dimensions = area && row.width_mm && row.height_mm ? ' · ' + number(row.width_mm, 1) + ' × ' + number(row.height_mm, 1) + ' mm' : ''
    const key = JSON.stringify([row.material_code, dimensions, row.unit, row.unit_price])
    if (bar) {
      rows.set(row.material_code, {code: row.material_code, description: bar.description, quantity: bar.bars_required, unit: 'barras', price: bar.purchase_cost / (bar.purchased_length_mm / 1000), basis: 'm', total: bar.purchase_cost})
      continue
    }
    const entry = rows.get(key) || {code: row.material_code, description: row.description + dimensions, quantity: 0, unit: area && dimensions ? 'peças' : row.unit, basis: row.unit, price: row.unit_price, total: 0}
    const amount = row.quantity_order * (area ? row.area_m2 ?? 1 : row.unit === 'm' && row.length_mm != null ? row.length_mm / 1000 : 1)
    entry.quantity += area && dimensions ? row.quantity_order : amount
    entry.total += amount * row.unit_price
    rows.set(key, entry)
  }
  return <section><p>{quote.client} · Orçamento {quote.number}</p>
    {rows.size ? <div className="table-scroll"><table><thead><tr>{['Descrição','Quantidade','Código','Preço unitário','Total'].map(label => <th key={label}>{label}</th>)}</tr></thead>
    <tbody>{Array.from(rows, ([key,r]) => <tr key={key}><td>{r.description}</td><td>{number(r.quantity, 3)} {r.unit}</td><td>{r.code}</td><td>{money(r.price)} / {r.basis}</td><td>{money(r.total)}</td></tr>)}</tbody>
    <tfoot><tr><th colSpan="4">Total do pedido</th><td>{money(Array.from(rows.values()).reduce((sum,r) => sum + r.total, 0))}</td></tr></tfoot></table></div> : <p>{data ? 'Nenhum material deste grupo no pedido.' : 'Aguardando cálculo do pedido.'}</p>}
  </section>
}
