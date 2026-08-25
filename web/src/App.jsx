import { useEffect, useMemo, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const baseDefaults = {
  quantity: 1,
  leaf_count: 2,
  application: 'JANELA',
  closure_mode: 'MAÇANETA COM CREMONA + FECHO OCULTO',
  cremona_base: 'CREMONA 1 PONTO',
  roller_description: 'ROLDANA 30KG',
  internal_finish: 'GUARNIÇÃO DE 70MM',
  external_finish: 'BARRA CHATA DE 30MM',
  screen_enabled: false,
  shutter_enabled: false,
}

const fallbackOptions = {
  leaf_systems: [
    { value: 'PRIME_WINDOW_42x66', label: 'Prime Janela 42x66' },
    { value: 'PRIME_DOOR_42x88', label: 'Prime Porta 42x88' },
    { value: 'DESIGN_DOOR_60x111', label: 'Design 60x111' },
  ],
  applications: ['JANELA', 'PORTA'],
  leaf_counts: [2, 3, 4, 6],
  glasses: [
    { description: '04mm FLOAT INCOLOR' },
    { description: '05mm FLOAT FUMÊ' },
  ],
  closures: [
    'MAÇANETA COM CREMONA + FECHO OCULTO',
    'MAÇANETA COM CREMONA + MAÇANETA OCULTA COM CREMONA',
    'MAÇANETA COM CREMONA',
  ],
  cremonas: ['CREMONA 1 PONTO'],
  rollers: ['ROLDANA 30KG', 'ROLDANA 50KG', 'ROLDANA 80KG', 'ROLDANA 120KG', 'ROLDANA 150KG'],
  finishes: ['SEM ACABAMENTO', 'GUARNIÇÃO DE 70MM', 'BARRA CHATA DE 30MM'],
  screen: { supported: true },
  shutter: { supported: 'partial', box_height_mm: 200 },
}

const initialItems = [
  {
    ...baseDefaults,
    id: crypto.randomUUID(),
    width_mm: 3500,
    height_mm: 2000,
    leaf_system: 'PRIME_WINDOW_42x66',
    glass_description: '04mm FLOAT INCOLOR',
  },
  {
    ...baseDefaults,
    id: crypto.randomUUID(),
    width_mm: 2000,
    height_mm: 2000,
    leaf_system: 'DESIGN_DOOR_60x111',
    glass_description: '04mm FLOAT INCOLOR',
  },
  {
    ...baseDefaults,
    id: crypto.randomUUID(),
    width_mm: 1500,
    height_mm: 3000,
    leaf_system: 'PRIME_WINDOW_42x66',
    glass_description: '05mm FLOAT FUMÊ',
    closure_mode: 'MAÇANETA COM CREMONA',
    roller_description: 'ROLDANA 50KG',
  },
  {
    ...baseDefaults,
    id: crypto.randomUUID(),
    width_mm: 2000,
    height_mm: 2000,
    leaf_system: 'PRIME_WINDOW_42x66',
    glass_description: '04mm FLOAT INCOLOR',
  },
]

const tabs = ['Custo por Grupo', 'BOM / Consumo', 'Compra de Barras', 'Plano de Corte', 'Alertas']

const money = (value = 0) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value || 0))

const number = (value = 0, digits = 2) =>
  new Intl.NumberFormat('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(value || 0))

const modelLabel = (system) => ({
  PRIME_WINDOW_42x66: 'Correr Prime 42x66',
  PRIME_DOOR_42x88: 'Correr Prime 42x88',
  DESIGN_DOOR_60x111: 'Correr Design 60x111',
}[system] || system)

function Sidebar() {
  const groups = [
    ['PRINCIPAL', ['Dashboard', 'Novo Cliente / Orçamento', 'Buscar Cliente / Orçamento', 'Visualizar Orçamentos', 'Visualizar Orçamento Resumido']],
    ['MODELOS E ITENS', ['Inserir Modelo Correr', 'Inserir Modelo Maxim-Ar', 'Inserir Modelo Giro', 'Inserir Modelo Fixo', 'Inserir Modelo Pivotante', 'Inserir Grade', 'Inserir Item Manualmente', 'Substituir Valor Manualmente', 'Definir Margem']],
    ['CADASTROS E CONFIGURAÇÕES', ['Materiais', 'Clientes', 'Configurações']],
  ]

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">▦</div><div><strong>Software</strong> Esquadrias</div></div>
      {groups.map(([title, items]) => (
        <div className="nav-group" key={title}>
          <div className="nav-title">{title}</div>
          {items.map((item, index) => (
            <button key={item} className={`nav-item ${item === 'Novo Cliente / Orçamento' ? 'active' : ''}`}>
              <span>{['◫','＋','⌕','▤','▥'][index % 5]}</span>{item}
            </button>
          ))}
        </div>
      ))}
      <button className="collapse">« Recolher menu</button>
    </aside>
  )
}

function Header({ apiOnline }) {
  return (
    <header className="topbar">
      <select className="company-select"><option>Empresa Demo</option></select>
      <div className="global-search">⌕ <input placeholder="Buscar clientes, orçamentos, modelos, itens..." /><kbd>Ctrl + K</kbd></div>
      <div className="header-actions">
        <span className={`api-dot ${apiOnline ? 'online' : 'offline'}`}></span>
        <span className="api-label">API {apiOnline ? 'online' : 'offline'}</span>
        <div className="avatar">AD</div>
        <div><strong>Administrador</strong><small>admin@demo.com</small></div>
      </div>
    </header>
  )
}

function ClientCard({ quote, setQuote }) {
  const set = (key) => (event) => setQuote((prev) => ({ ...prev, [key]: event.target.value }))
  return (
    <section className="card client-card">
      <div className="section-title">♙ Dados do Cliente e Orçamento</div>
      <div className="form-grid">
        <label>Cliente *<input value={quote.client} onChange={set('client')} /></label>
        <label>Telefone<input value={quote.phone} onChange={set('phone')} /></label>
        <label>Cidade<input value={quote.city} onChange={set('city')} /></label>
        <label>Data *<input type="date" value={quote.date} onChange={set('date')} /></label>
        <label>Nº do orçamento *<input value={quote.number} onChange={set('number')} /></label>
        <label className="span-3">Obra<input value={quote.project} onChange={set('project')} /></label>
        <label className="span-4">Observações<textarea value={quote.notes} onChange={set('notes')} /></label>
      </div>
    </section>
  )
}

function ItemsTable({ items, onRemove, onAdd, onEdit }) {
  return (
    <section className="card items-card">
      <div className="section-head">
        <div className="section-title">Itens do Orçamento</div>
        <button className="primary" onClick={onAdd}>＋ Inserir Modelo Correr</button>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Item</th><th>Tipo</th><th>Aplicação</th><th>Folhas</th><th>Largura</th><th>Altura</th><th>Qtd</th><th>Vidro</th><th>Tela</th><th>Persiana</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={item.id}>
                <td><strong>{String(index + 1).padStart(2, '0')}</strong></td>
                <td>{modelLabel(item.leaf_system)}</td>
                <td>{item.application === 'JANELA' ? 'Janela' : 'Porta'}</td>
                <td>{item.leaf_count}</td>
                <td>{item.width_mm}</td>
                <td>{item.height_mm}</td>
                <td>{item.quantity}</td>
                <td>{item.glass_description.replace(' FLOAT ', ' ')}</td>
                <td>{item.screen_enabled ? 'Sim' : 'Não'}</td>
                <td>{item.shutter_enabled ? 'Sim' : 'Não'}</td>
                <td><span className="status">● Calculado</span></td>
                <td><button className="icon-btn" title="Editar" onClick={() => onEdit(item)}>✎</button><button className="icon-btn danger" title="Excluir" onClick={() => onRemove(item.id)}>⌫</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">Exibindo {items.length} de {items.length} itens</div>
    </section>
  )
}

function Summary({ data, margin, setMargin }) {
  const plan = data?.purchase_plan
  const suggested = (plan?.procurement_total_estimate || 0) / Math.max(0.01, 1 - margin / 100)
  return (
    <aside className="summary-column">
      <div className="kpi-grid">
        <Kpi label="Itens" value={data?.items?.length || 0} tone="blue" />
        <Kpi label="Alertas" value={(plan?.warnings?.length || 0) + (data?.items || []).flatMap((i) => i.warnings || []).length} tone="amber" />
        <Kpi label="Aproveitamento" value={`${number(globalUtilization(plan), 2)}%`} tone="green" />
        <Kpi label="Barras" value={totalBars(plan)} tone="purple" />
      </div>
      <section className="card summary-card">
        <div className="section-title">▤ Resumo do Orçamento</div>
        <SummaryLine label="Custo técnico" value={money(plan?.technical_total)} />
        <SummaryLine label="Compra de barras" value={money(plan?.bar_stock_purchase_cost)} />
        <SummaryLine label="Materiais não lineares" value={money(plan?.exact_nonbar_cost)} />
        <div className="summary-divider" />
        <SummaryLine label="Compra estimada" value={money(plan?.procurement_total_estimate)} strong />
        <label className="margin-row">Margem<input type="number" min="0" max="90" value={margin} onChange={(e) => setMargin(Number(e.target.value))} /><span>%</span></label>
        <div className="sale-price"><span>Preço de venda sugerido</span><strong>{money(suggested)}</strong></div>
      </section>
      {plan?.warnings?.map((warning) => <div className="warning-card" key={warning.code}><strong>⚠ {warning.code}</strong><span>{warning.message}</span></div>)}
    </aside>
  )
}

function Kpi({ label, value, tone }) {
  return <div className={`kpi ${tone}`}><span>{label}</span><strong>{value}</strong></div>
}

function SummaryLine({ label, value, strong }) {
  return <div className={`summary-line ${strong ? 'strong' : ''}`}><span>{label}</span><strong>{value}</strong></div>
}

function globalUtilization(plan) {
  if (!plan?.lines?.length) return 0
  const consumed = plan.lines.reduce((sum, line) => sum + (line.consumed_length_mm || 0), 0)
  const purchased = plan.lines.reduce((sum, line) => sum + (line.purchased_length_mm || 0), 0)
  return purchased ? (consumed / purchased) * 100 : 0
}

function totalBars(plan) {
  return plan?.lines?.reduce((sum, line) => sum + (line.bars_required || 0), 0) || 0
}

function Analysis({ data, activeTab, setActiveTab }) {
  const allWarnings = [
    ...(data?.purchase_plan?.warnings || []),
    ...(data?.items || []).flatMap((item) => item.warnings || []),
  ]

  return (
    <section className="card analysis-card">
      <div className="tabs">
        {tabs.map((tab) => <button key={tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab}{tab === 'Alertas' && allWarnings.length ? <em>{allWarnings.length}</em> : null}</button>)}
      </div>
      <div className="tab-body">
        {activeTab === 'Custo por Grupo' && <CostGroups items={data?.items || []} />}
        {activeTab === 'BOM / Consumo' && <BomTable items={data?.items || []} />}
        {activeTab === 'Compra de Barras' && <PurchaseTable plan={data?.purchase_plan} />}
        {activeTab === 'Plano de Corte' && <CutPlan plan={data?.purchase_plan} />}
        {activeTab === 'Alertas' && <Warnings warnings={allWarnings} />}
      </div>
    </section>
  )
}

function CostGroups({ items }) {
  const groups = useMemo(() => {
    const acc = {}
    items.forEach((item) => Object.entries(item.cost_by_group || {}).forEach(([key, value]) => {
      if (key !== 'TOTAL') acc[key] = (acc[key] || 0) + Number(value || 0) * Number(item.quantity || 1)
    }))
    return Object.entries(acc).sort((a, b) => b[1] - a[1])
  }, [items])
  const total = groups.reduce((sum, [, value]) => sum + value, 0)
  return <div className="group-list">{groups.map(([group, value]) => <div className="group-row" key={group}><span className="group-name">● {group}</span><strong>{money(value)}</strong><span>{total ? number((value / total) * 100, 2) : '0,00'}%</span><div className="bar-track"><div className="bar-fill" style={{ width: `${total ? (value / total) * 100 : 0}%` }} /></div></div>)}</div>
}

function BomTable({ items }) {
  const rows = items.flatMap((item, idx) => (item.bom || []).map((bom) => ({ ...bom, item: idx + 1 })))
  return <div className="table-scroll"><table><thead><tr><th>Item</th><th>Grupo</th><th>Código</th><th>Descrição</th><th>Qtd pedido</th><th>Un.</th><th>Custo</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.item}-${row.material_code}-${index}`}><td>{row.item}</td><td>{row.category}</td><td>{row.material_code}</td><td>{row.description}</td><td>{number(row.quantity_order, 3)}</td><td>{row.unit}</td><td>{money(row.cost_per_unit_product)}</td></tr>)}</tbody></table></div>
}

function PurchaseTable({ plan }) {
  return <div className="table-scroll"><table><thead><tr><th>Código</th><th>Descrição</th><th>Cortes</th><th>Consumo</th><th>Barras 5.900</th><th>Comprado</th><th>Sobra</th><th>Aproveit.</th><th>Custo compra</th></tr></thead><tbody>{(plan?.lines || []).map((line) => <tr key={line.material_code}><td><strong>{line.material_code}</strong></td><td>{line.description}</td><td>{line.pieces_count}</td><td>{number(line.consumed_length_mm / 1000, 3)} m</td><td>{line.bars_required}</td><td>{number(line.purchased_length_mm / 1000, 3)} m</td><td>{number(line.waste_length_mm / 1000, 3)} m</td><td>{number(line.utilization_pct, 2)}%</td><td>{money(line.purchase_cost)}</td></tr>)}</tbody></table></div>
}

function CutPlan({ plan }) {
  return <div className="cut-grid">{(plan?.lines || []).map((line) => <div className="cut-material" key={line.material_code}><div className="cut-head"><strong>{line.material_code}</strong><span>{line.bars_required} barra(s)</span></div>{(line.bars || []).map((bar) => <div className="cut-bar" key={bar.bar_number}><div className="cut-label">Barra {bar.bar_number} · 5.900 mm</div><div className="cut-pieces">{bar.pieces.map((piece, index) => <span key={`${piece.source_item}-${index}`}>{number(piece.length_mm, 0)} mm · I{piece.source_item}</span>)}</div></div>)}</div>)}</div>
}

function Warnings({ warnings }) {
  if (!warnings.length) return <div className="empty-state">Nenhum alerta para este orçamento.</div>
  return <div className="warnings-list">{warnings.map((warning, index) => <div className="warning-row" key={`${warning.code}-${index}`}><strong>{warning.code}</strong><span>{warning.message}</span></div>)}</div>
}

function FieldSection({ title, children }) {
  return <div className="field-section"><div className="field-section-title">{title}</div><div className="modal-grid">{children}</div></div>
}

function AddItemModal({ onClose, onSave, options, item }) {
  const [form, setForm] = useState(() => item ? { ...item } : {
    ...baseDefaults,
    width_mm: 1200,
    height_mm: 1200,
    leaf_system: 'PRIME_WINDOW_42x66',
    glass_description: '04mm FLOAT INCOLOR',
  })
  const [validation, setValidation] = useState('')

  const set = (key) => (event) => {
    const target = event.target
    let value = target.type === 'checkbox' ? target.checked : target.value
    if (target.type === 'number' || key === 'leaf_count' || key === 'quantity') value = Number(value)
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const submit = (event) => {
    event.preventDefault()
    if (form.width_mm <= 0 || form.height_mm <= 0) return setValidation('Largura e altura precisam ser maiores que zero.')
    if (form.quantity < 1) return setValidation('Quantidade deve ser pelo menos 1.')
    setValidation('')
    onSave({ ...form, id: item?.id || crypto.randomUUID() })
  }

  const shutterHeight = options?.shutter?.box_height_mm || 200

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form className="modal modal-large" onSubmit={submit} onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div><strong>{item ? 'Editar Modelo Correr' : 'Inserir Modelo Correr'}</strong><span>Configuração técnica CR conectada à Engine</span></div>
          <button type="button" onClick={onClose}>×</button>
        </div>
        <div className="modal-scroll">
          {validation && <div className="error-banner compact">⚠ {validation}</div>}

          <FieldSection title="Medidas e sistema">
            <label>Largura (mm)<input type="number" min="1" value={form.width_mm} onChange={set('width_mm')} /></label>
            <label>Altura (mm)<input type="number" min="1" value={form.height_mm} onChange={set('height_mm')} /></label>
            <label>Quantidade<input type="number" min="1" value={form.quantity} onChange={set('quantity')} /></label>
            <label>Tipo de folha<select value={form.leaf_system} onChange={set('leaf_system')}>{options.leaf_systems.map((row) => <option key={row.value} value={row.value}>{row.label}</option>)}</select></label>
            <label>Aplicação<select value={form.application} onChange={set('application')}>{options.applications.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Nº de folhas<select value={form.leaf_count} onChange={set('leaf_count')}>{options.leaf_counts.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
          </FieldSection>

          <FieldSection title="Vidro e complementos">
            <label className="span-2">Vidro<select value={form.glass_description} onChange={set('glass_description')}>{options.glasses.map((glass) => <option key={`${glass.code || ''}-${glass.description}`} value={glass.description}>{glass.description}{glass.price != null ? ` · ${money(glass.price)}/m²` : ''}</option>)}</select></label>
            <label className="toggle-field"><span>Tela mosquiteira</span><input type="checkbox" checked={form.screen_enabled} onChange={set('screen_enabled')} /></label>
            <label className="toggle-field"><span>Persiana</span><input type="checkbox" checked={form.shutter_enabled} onChange={set('shutter_enabled')} /></label>
            {form.shutter_enabled && <label>Caixa da persiana<input value={`${number(shutterHeight, 0)} mm`} readOnly /></label>}
            {form.shutter_enabled && <div className="info-note">A caixa de {number(shutterHeight, 0)} mm já altera a geometria do cálculo. O kit completo da persiana ainda está marcado como migração pendente do Excel.</div>}
          </FieldSection>

          <FieldSection title="Fechamento e ferragens">
            <label className="span-2">Fechamento<select value={form.closure_mode} onChange={set('closure_mode')}>{options.closures.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Cremona<select value={form.cremona_base} onChange={set('cremona_base')}>{options.cremonas.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Roldanas<select value={form.roller_description} onChange={set('roller_description')}>{options.rollers.map((value) => <option key={value}>{value}</option>)}</select></label>
          </FieldSection>

          <FieldSection title="Acabamentos">
            <label>Acabamento interno<select value={form.internal_finish} onChange={set('internal_finish')}>{options.finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Acabamento externo<select value={form.external_finish} onChange={set('external_finish')}>{options.finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
          </FieldSection>
        </div>
        <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary" type="submit">{item ? 'Salvar e recalcular' : 'Adicionar e recalcular'}</button></div>
      </form>
    </div>
  )
}

export default function App() {
  const [items, setItems] = useState(() => {
    const saved = localStorage.getItem('software-esquadrias-items')
    return saved ? JSON.parse(saved) : initialItems
  })
  const [quote, setQuote] = useState(() => {
    const saved = localStorage.getItem('software-esquadrias-quote')
    return saved ? JSON.parse(saved) : {
      client: 'João da Silva Construções Ltda.', phone: '(51) 99999-0000', city: 'Gravataí - RS', date: new Date().toISOString().slice(0, 10),
      number: '000001/2026', project: 'Obra piloto — Dell Amanda', notes: 'Pedido de validação da Engine CR e plano de compra.',
    }
  })
  const [margin, setMargin] = useState(25)
  const [activeTab, setActiveTab] = useState('Custo por Grupo')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiOnline, setApiOnline] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [options, setOptions] = useState(fallbackOptions)

  useEffect(() => { localStorage.setItem('software-esquadrias-items', JSON.stringify(items)) }, [items])
  useEffect(() => { localStorage.setItem('software-esquadrias-quote', JSON.stringify(quote)) }, [quote])

  const loadOptions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/engine/cr/options`)
      if (!response.ok) throw new Error('Falha ao carregar opções')
      setOptions(await response.json())
    } catch {
      setOptions(fallbackOptions)
    }
  }

  const calculate = async (nextItems = items) => {
    if (!nextItems.length) { setData(null); return }
    setLoading(true); setError('')
    try {
      const payload = { items: nextItems.map(({ id, ...item }) => item) }
      const response = await fetch(`${API_URL}/api/v1/purchase-plans/calculate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail || `API respondeu ${response.status}`)
      }
      const result = await response.json()
      setData(result); setApiOnline(true)
    } catch (err) {
      setApiOnline(false); setError(`Não foi possível calcular: ${err.message}. Confirme se a API está rodando na porta 8000.`)
    } finally { setLoading(false) }
  }

  useEffect(() => { loadOptions(); calculate(items) }, [])

  const removeItem = (id) => {
    const next = items.filter((item) => item.id !== id)
    setItems(next); calculate(next)
  }

  const saveItem = (item) => {
    const exists = items.some((current) => current.id === item.id)
    const next = exists ? items.map((current) => current.id === item.id ? item : current) : [...items, item]
    setItems(next); setModalOpen(false); setEditingItem(null); calculate(next)
  }

  const openNew = () => { setEditingItem(null); setModalOpen(true) }
  const openEdit = (item) => { setEditingItem(item); setModalOpen(true) }

  const resetBaseline = () => {
    setItems(initialItems); calculate(initialItems)
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="workspace">
        <Header apiOnline={apiOnline} />
        <main className="content">
          <div className="page-head"><div><span className="eyebrow">ORÇAMENTO</span><h1>Novo Cliente / Orçamento</h1><p>Monte o pedido, calcule custos técnicos e gere o plano de compra.</p></div><div className="page-actions"><button className="secondary" onClick={resetBaseline}>Restaurar teste validado</button><button className="primary" onClick={() => calculate()} disabled={loading}>{loading ? 'Calculando...' : '↻ Recalcular pedido'}</button></div></div>
          {error && <div className="error-banner">⚠ {error}</div>}
          <div className="dashboard-grid">
            <div className="main-column">
              <ClientCard quote={quote} setQuote={setQuote} />
              <ItemsTable items={items} onRemove={removeItem} onAdd={openNew} onEdit={openEdit} />
              <Analysis data={data} activeTab={activeTab} setActiveTab={setActiveTab} />
            </div>
            <Summary data={data} margin={margin} setMargin={setMargin} />
          </div>
        </main>
      </div>
      {modalOpen && <AddItemModal onClose={() => { setModalOpen(false); setEditingItem(null) }} onSave={saveItem} options={options} item={editingItem} />}
    </div>
  )
}
