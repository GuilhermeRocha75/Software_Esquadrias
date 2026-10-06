import { useEffect, useMemo, useState } from 'react'

import { sidebarModelAction } from './sidebarActions.js'

const API_URL = (import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000')).replace(/\/$/, '')

const baseDefaults = {
  family: 'CR',
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
  shutter: {
    mode: 'SEM PERSIANA',
    box_description: 'CAIXA DE 200MM',
    slat_description: 'TALA DE PVC 40MM',
  },
  leaf_grid: { horizontal_transoms: 0, vertical_transoms: 0, custom_dimensions: [] },
  bottom_fixed_panel: null,
  top_fixed_panel: null,
  structural_reinforcement: null,
}

const maximArDefaults = {
  family: 'MAXIM_AR',
  quantity: 1,
  leaf_count: 1,
  width_mm: 800,
  height_mm: 800,
  leaf_system: 'PRIME_WINDOW_42x63',
  orientation: 'HORIZONTAL',
  module_mode: 'MÓDULO ÚNICO',
  glass_description: '04mm MINI BOREAL',
  closure_mode: 'FECHO 1 PONTO',
  cremona_description: null,
  internal_finish: 'GUARNIÇÃO DE 70MM',
  external_finish: 'BARRA CHATA DE 30MM',
  screen_enabled: false,
  leaf_grid: { horizontal_transoms: 0, vertical_transoms: 0, custom_dimensions: [] },
  bottom_fixed_panel: null,
  top_fixed_panel: null,
  structural_reinforcement: null,
  sealing: { internal_material_id: 'MX-SEALING-CONFIGURABLE', description: 'VEDAÇÃO MAXIM-AR CONFIGURÁVEL', unit_price_per_meter: 0 },
}

const grDefaults = {
  family: 'GR',
  quantity: 1,
  leaf_count: 1,
  width_mm: 900,
  height_mm: 2100,
  leaf_system: 'FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN',
  application: 'PORTA',
  panel_mode: 'PAINEL COMPLETO',
  glass_description: null,
  custom_glass_code: null,
  custom_glass_unit_price: null,
  custom_glass_thickness_mm: null,
  mixed_split_from_bottom_mm: null,
  module_mode: 'MÓDULO ÚNICO',
  closure_mode: 'MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE',
  cremona_description: null,
  hinge_description: 'DOBRADIÇA 90MM',
  window_lock_length_mm: null,
  shutter: null,
  screen_enabled: false,
  top_flag_height_mm: 0,
  bottom_flag_height_mm: 0,
  bottom_flag_vertical_transoms: 0,
  bottom_flag_horizontal_transoms: 0,
  top_flag_vertical_transoms: 0,
  top_flag_horizontal_transoms: 0,
  internal_finish: 'GUARNIÇÃO DE 70MM',
  external_finish: 'BARRA CHATA DE 30MM',
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
  shutter: {
    supported: true,
    box_height_mm: 200,
    modes: [
      'SEM PERSIANA',
      'MANUAL EM PAINEL ÚNICO',
      'MANUAL EM 2 PAINÉIS COM EIXO ÚNICO',
      'MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES',
      'AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO',
      'AUTOMATIZADA COM BOTOEIRA EM 2 PAINÉIS',
      'AUTOMATIZADA COM BOTOEIRA EM 3 PAINÉIS',
      'AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO',
      'AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS',
      'AUTOMATIZADA COM CONTROLE REMOTO EM 3 PAINÉIS',
    ],
    boxes: ['CAIXA DE 200MM'],
    slats: ['TALA DE PVC 40MM'],
  },
}

const fallbackMaximArOptions = {
  leaf_systems: [
    { value: 'PRIME_WINDOW_42x63', label: 'Prime Janela 42x63' },
    { value: 'DESIGN_WINDOW_60x78', label: 'Design Janela 60x78' },
  ],
  leaf_counts: [1, 2, 3, 4, 5, 6, 7, 8],
  orientations: ['HORIZONTAL', 'VERTICAL'],
  module_modes: ['MÓDULO ÚNICO', 'MÓDULOS SEPARADOS'],
  glasses: [{ description: '04mm MINI BOREAL', compatible_systems: ['PRIME_WINDOW_42x63', 'DESIGN_WINDOW_60x78'] }],
  closures: ['FECHO 1 PONTO', 'MAÇANETA COM CREMONA'],
  cremonas: [
    'CREMONA MAXIM-AR 2 PONTOS COMP. 300mm',
    'CREMONA MAXIM-AR 2 PONTOS COMP. 400mm',
    'CREMONA MAXIM-AR 2 PONTOS COMP. 600mm',
    'CREMONA MAXIM-AR 2 PONTOS COMP. 800mm',
  ],
  internal_finishes: ['GUARNIÇÃO DE 70MM'],
  external_finishes: ['BARRA CHATA DE 30MM'],
}

const fallbackGrOptions = {
  leaf_systems: [
    { value: 'FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN', label: 'Porta Design 60x104 — abertura interna' },
    { value: 'FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN', label: 'Porta Design 60x104 — abertura externa' },
    { value: 'FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN', label: 'Janela Design 60x78 — abertura externa' },
  ],
  applications: ['PORTA', 'JANELA'],
  leaf_counts: [1, 2],
  panel_modes: ['PAINEL COMPLETO', 'VIDRO INTEIRO', 'SUPERIOR VIDRO/INFERIOR PAINEL'],
  glasses: [{ description: '04mm FLOAT INCOLOR' }, { description: '06mm TEMPERADO INCOLOR' }],
  closures: [
    'MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE',
    'MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE',
    'MAÇANETA COM CREMONA SEM CHAVE',
    'MAÇANETA COM CHAVE E CREMONA',
    'MAÇANETA COM CREMONA',
  ],
  cremonas: {
    standard_options: ['CREMONA 2 PONTOS COMP. 800mm E:15mm'],
    ob_options: [
      'CREMONA OSCILO/GIRO COMP. 400mm E:15mm',
      'CREMONA OSCILO/GIRO COMP. 900mm E:15mm',
      'CREMONA OSCILO/GIRO COMP. 1100mm E:15mm',
      'CREMONA OSCILO/GIRO COMP. 1400mm E:15mm',
      'CREMONA OSCILO/GIRO COMP. 1900mm E:15mm',
    ],
  },
  hinges: ['DOBRADIÇA 90MM', 'DOBRADIÇA SISTEMA OB', 'DOBRADIÇA PÊRNIO'],
  shutter: {
    modes: [
      'MANUAL EM PAINEL ÚNICO',
      'AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO',
      'AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO',
      'MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES',
    ],
    box_description: 'CAIXA DE 200MM',
    slat_description: 'TALA DE PVC 40MM',
  },
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

const modelLabel = (item) => ({
  PRIME_WINDOW_42x66: 'Correr Prime 42x66',
  PRIME_DOOR_42x88: 'Correr Prime 42x88',
  DESIGN_DOOR_60x111: 'Correr Design 60x111',
  PRIME_WINDOW_42x63: 'Maxim-Ar Prime 42x63',
  DESIGN_WINDOW_60x78: 'Maxim-Ar Design 60x78',
  'FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN': 'Giro GR 60x104 interna',
  'FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN': 'Giro GR 60x104 externa',
  'FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN': 'Giro GR janela 60x78',
}[item.leaf_system] || item.leaf_system)

function Sidebar({ onAddCR, onAddMaximAr, onAddGr }) {
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
            <button key={item} onClick={sidebarModelAction(item, { onAddCR, onAddMaximAr, onAddGr })} className={`nav-item ${item === 'Novo Cliente / Orçamento' ? 'active' : ''}`}>
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

function ItemsTable({ items, onRemove, onAddCR, onAddMaximAr, onAddGr, onEdit }) {
  return (
    <section className="card items-card">
      <div className="section-head">
        <div className="section-title">Itens do Orçamento</div>
        <div className="page-actions"><button className="secondary" onClick={onAddGr}>+ Inserir Giro GR</button><button className="secondary" onClick={onAddMaximAr}>+ Inserir Maxim-Ar</button><button className="primary" onClick={onAddCR}>＋ Inserir Modelo Correr</button></div>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Item</th><th>Tipo</th><th>Aplicação</th><th>Folhas</th><th>Largura</th><th>Altura</th><th>Qtd</th><th>Vidro</th><th>Tela</th><th>Persiana</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={item.id}>
                <td><strong>{String(index + 1).padStart(2, '0')}</strong></td>
                <td>{modelLabel(item)}</td>
                <td>{item.family === 'MAXIM_AR' || item.application === 'JANELA' ? 'Janela' : 'Porta'}</td>
                <td>{item.leaf_count}</td>
                <td>{item.width_mm}</td>
                <td>{item.height_mm}</td>
                <td>{item.quantity}</td>
                <td>{item.glass_description?.replace(' FLOAT ', ' ') || 'Painel'}</td>
                <td>{item.screen_enabled ? 'Sim' : 'Não'}</td>
                <td>{item.shutter?.mode && item.shutter.mode !== 'SEM PERSIANA' ? item.shutter.mode : (item.shutter_enabled ? 'Legado' : 'Não')}</td>
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

function MaximArModal({ onClose, onSave, options, item }) {
  const [form, setForm] = useState(() => ({ ...maximArDefaults, ...(item || {}) }))
  const [validation, setValidation] = useState('')
  const set = (key) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : (event.target.type === 'number' || key === 'leaf_count') ? Number(event.target.value) : event.target.value
    setForm((previous) => ({
      ...previous,
      [key]: value,
      ...(key === 'closure_mode' && value === 'FECHO 1 PONTO' ? { cremona_description: null } : {}),
    }))
  }
  const togglePanel = (key) => (event) => setForm((previous) => {
    const enabled = event.target.checked
    const next = { ...previous, [key]: enabled ? { height_mm: 600, horizontal_transoms: 0, vertical_transoms: 0 } : null }
    if (!next.bottom_fixed_panel && !next.top_fixed_panel) {
      next.module_mode = 'MÓDULO ÚNICO'
      next.structural_reinforcement = null
    }
    return next
  })
  const setPanelHeight = (key) => (event) => setForm((previous) => ({
    ...previous,
    [key]: { ...previous[key], height_mm: Number(event.target.value) },
  }))
  const setFixedTransoms = (panel, axis) => (event) => setForm((previous) => ({
    ...previous,
    [panel]: { ...previous[panel], [axis]: Number(event.target.value) },
  }))
  const setStructural = (event) => setForm((previous) => ({
    ...previous,
    structural_reinforcement: event.target.value ? { material_code: event.target.value } : null,
  }))
  const compatibleGlasses = options.glasses.filter((glass) =>
    !glass.compatible_systems || glass.compatible_systems.includes(form.leaf_system))
  const submit = (event) => {
    event.preventDefault()
    if (form.width_mm <= 0 || form.height_mm <= 0) return setValidation('Largura e altura precisam ser maiores que zero.')
    if (form.quantity < 1) return setValidation('Quantidade deve ser pelo menos 1.')
    if (form.module_mode === 'MÓDULOS SEPARADOS' && !form.bottom_fixed_panel && !form.top_fixed_panel) return setValidation('Módulos separados exigem ao menos uma bandeira.')
    if ((form.leaf_grid.horizontal_transoms || form.leaf_grid.vertical_transoms)) return setValidation('AF/AG na folha móvel são fisicamente inválidos.')
    if (form.module_mode === 'MÓDULOS SEPARADOS' && [form.bottom_fixed_panel, form.top_fixed_panel].filter(Boolean).some((p) => p.horizontal_transoms || p.vertical_transoms)) return setValidation('Módulos separados não admitem travessas internas.')
    if (form.structural_reinforcement && form.module_mode !== 'MÓDULOS SEPARADOS') return setValidation('Reforço estrutural só é permitido em módulos separados.')
    if (form.closure_mode === 'MAÇANETA COM CREMONA' && !form.cremona_description) return setValidation('Selecione a cremona Maxim-Ar.')
    onSave({ ...form, family: 'MAXIM_AR', id: item?.id || crypto.randomUUID() })
  }
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form className="modal modal-large" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <div><strong>{item ? 'Editar Modelo Maxim-Ar' : 'Inserir Modelo Maxim-Ar'}</strong><span>Fase 3B conectada à MX_ENGINE_0.3.0</span></div>
          <button type="button" onClick={onClose}>×</button>
        </div>
        <div className="modal-scroll">
          {validation && <div className="error-banner compact">⚠ {validation}</div>}
          <FieldSection title="Medidas e sistema">
            <label>Largura (mm)<input type="number" min="1" value={form.width_mm} onChange={set('width_mm')} /></label>
            <label>Altura (mm)<input type="number" min="1" value={form.height_mm} onChange={set('height_mm')} /></label>
            <label>Quantidade<input type="number" min="1" value={form.quantity} onChange={set('quantity')} /></label>
            <label>Folhas<select value={form.leaf_count} onChange={set('leaf_count')}>{options.leaf_counts.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label>Tipo de folha<select value={form.leaf_system} onChange={set('leaf_system')}>{options.leaf_systems.map((row) => <option key={row.value} value={row.value}>{row.label}</option>)}</select></label>
            <label>Orientação<select value={form.orientation} onChange={set('orientation')}>{(options.orientations || ['HORIZONTAL', 'VERTICAL']).map((value) => <option key={value}>{value}</option>)}</select></label>
          </FieldSection>
          <FieldSection title="Vidro">
            <label className="span-2">Vidro<select value={form.glass_description} onChange={set('glass_description')}>{compatibleGlasses.map((glass) => <option key={`${glass.code || ''}-${glass.description}`} value={glass.description}>{glass.description}{glass.price != null ? ` · ${money(glass.price)}/m²` : ''}</option>)}</select></label>
            <label className="checkbox-row"><input type="checkbox" checked={form.screen_enabled} onChange={set('screen_enabled')} /> Tela recolhível TL3</label>
            <div className="info-note">A tela é um conjunto comprado: largura + altura + valor unitário, conforme MX!64.</div>
          </FieldSection>
          <FieldSection title="Bandeiras e módulos">
            <label className="checkbox-row"><input type="checkbox" checked={Boolean(form.bottom_fixed_panel)} onChange={togglePanel('bottom_fixed_panel')} /> Bandeira inferior</label>
            {form.bottom_fixed_panel && <label>Altura inferior (mm)<input type="number" min="1" value={form.bottom_fixed_panel.height_mm} onChange={setPanelHeight('bottom_fixed_panel')} /></label>}
            <label className="checkbox-row"><input type="checkbox" checked={Boolean(form.top_fixed_panel)} onChange={togglePanel('top_fixed_panel')} /> Bandeira superior</label>
            {form.top_fixed_panel && <label>Altura superior (mm)<input type="number" min="1" value={form.top_fixed_panel.height_mm} onChange={setPanelHeight('top_fixed_panel')} /></label>}
            {(form.bottom_fixed_panel || form.top_fixed_panel) && <label>Modo<select value={form.module_mode} onChange={set('module_mode')}>{(options.module_modes || ['MÓDULO ÚNICO', 'MÓDULOS SEPARADOS']).map((value) => <option key={value}>{value}</option>)}</select></label>}
            {form.bottom_fixed_panel && form.module_mode === 'MÓDULO ÚNICO' && <label>Travessas H/V inferior<div className="inline-inputs"><input type="number" min="0" value={form.bottom_fixed_panel.horizontal_transoms || 0} onChange={setFixedTransoms('bottom_fixed_panel', 'horizontal_transoms')} /><input type="number" min="0" value={form.bottom_fixed_panel.vertical_transoms || 0} onChange={setFixedTransoms('bottom_fixed_panel', 'vertical_transoms')} /></div></label>}
            {form.top_fixed_panel && form.module_mode === 'MÓDULO ÚNICO' && <label>Travessas H/V superior<div className="inline-inputs"><input type="number" min="0" value={form.top_fixed_panel.horizontal_transoms || 0} onChange={setFixedTransoms('top_fixed_panel', 'horizontal_transoms')} /><input type="number" min="0" value={form.top_fixed_panel.vertical_transoms || 0} onChange={setFixedTransoms('top_fixed_panel', 'vertical_transoms')} /></div></label>}
            {(form.bottom_fixed_panel || form.top_fixed_panel) && <label>Reforço estrutural<select disabled={form.module_mode !== 'MÓDULOS SEPARADOS'} value={form.structural_reinforcement?.material_code || ''} onChange={setStructural}><option value="">Sem reforço</option><option value="ALUM10238">ALUM10238 · 102x50</option><option value="ALUM15338">ALUM15338 · 138x50</option></select></label>}
            <div className="info-note">Travessas pertencem apenas a bandeiras integradas. Reforço estrutural é opcional e exclusivo de módulos separados.</div>
          </FieldSection>
          <FieldSection title="Vedação configurável">
            <label className="span-2">Descrição<input value={form.sealing.description} onChange={(e) => setForm((p) => ({ ...p, sealing: { ...p.sealing, description: e.target.value } }))} /></label>
            <label>Identificador interno<input value={form.sealing.internal_material_id} onChange={(e) => setForm((p) => ({ ...p, sealing: { ...p.sealing, internal_material_id: e.target.value } }))} /></label>
            <label>Preço por metro<input type="number" min="0" step="0.01" value={form.sealing.unit_price_per_meter} onChange={(e) => setForm((p) => ({ ...p, sealing: { ...p.sealing, unit_price_per_meter: Number(e.target.value) } }))} /></label>
          </FieldSection>
          <FieldSection title="Fechamento e ferragens">
            <label className="span-2">Fechamento<select value={form.closure_mode} onChange={set('closure_mode')}>{options.closures.map((value) => <option key={value}>{value}</option>)}</select></label>
            {form.closure_mode === 'MAÇANETA COM CREMONA' && <label className="span-2">Cremona<select value={form.cremona_description || ''} onChange={set('cremona_description')}><option value="">Selecione</option>{options.cremonas.map((value) => <option key={value}>{value}</option>)}</select></label>}
          </FieldSection>
          <FieldSection title="Acabamentos comprovados">
            <label>Interno<select value={form.internal_finish} onChange={set('internal_finish')}>{options.internal_finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Externo<select value={form.external_finish} onChange={set('external_finish')}>{options.external_finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
          </FieldSection>
        </div>
        <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary" type="submit">{item ? 'Salvar e recalcular' : 'Adicionar e recalcular'}</button></div>
      </form>
    </div>
  )
}

function GrModal({ onClose, onSave, options, item }) {
  const [form, setForm] = useState(() => ({ ...grDefaults, ...(item || {}) }))
  const [customGlass, setCustomGlass] = useState(Boolean(item?.custom_glass_code))
  const [validation, setValidation] = useState('')
  const numericFields = new Set([
    'width_mm', 'height_mm', 'quantity', 'leaf_count', 'mixed_split_from_bottom_mm',
    'window_lock_length_mm', 'top_flag_height_mm', 'bottom_flag_height_mm',
    'bottom_flag_vertical_transoms', 'top_flag_vertical_transoms',
    'custom_glass_unit_price', 'custom_glass_thickness_mm',
  ])
  const set = (key) => (event) => {
    const raw = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    const value = numericFields.has(key) ? (raw === '' ? null : Number(raw)) : raw
    setForm((previous) => ({ ...previous, [key]: value }))
  }
  const setShutter = (event) => {
    const mode = event.target.value
    setForm((previous) => ({
      ...previous,
      shutter: mode === 'SEM PERSIANA' ? null : {
        mode,
        box_description: 'CAIXA DE 200MM',
        slat_description: 'TALA DE PVC 40MM',
      },
    }))
  }
  const setCatalogGlass = (event) => {
    const value = event.target.value
    if (value === '__CUSTOM__') {
      setCustomGlass(true)
      setForm((previous) => ({
        ...previous,
        glass_description: '',
        custom_glass_code: '',
        custom_glass_unit_price: null,
        custom_glass_thickness_mm: null,
      }))
    } else {
      setCustomGlass(false)
      setForm((previous) => ({
        ...previous,
        glass_description: value || null,
        custom_glass_code: null,
        custom_glass_unit_price: null,
        custom_glass_thickness_mm: null,
      }))
    }
  }
  const usesCremona = form.closure_mode.includes('CREMONA')
  const isPhysicalWindow = form.leaf_system.includes('FOLHA DE JANELA')
  const usesWindowLock = isPhysicalWindow && (
    form.closure_mode.includes('MONOPONTO') || form.closure_mode.includes('MULTIPONTO')
  )
  const closureOptions = isPhysicalWindow
    ? options.closures.filter((value) => value !== 'MAÇANETA COM CHAVE E CREMONA')
    : options.closures
  const hasFlag = Number(form.bottom_flag_height_mm || 0) > 0 || Number(form.top_flag_height_mm || 0) > 0
  const needsGlass = form.panel_mode !== 'PAINEL COMPLETO' || hasFlag
  const cremonaOptions = form.hinge_description === 'DOBRADIÇA SISTEMA OB'
    ? (options.cremonas?.ob_options || [])
    : (options.cremonas?.standard_options || [])
  const submit = (event) => {
    event.preventDefault()
    if (form.width_mm <= 0 || form.height_mm <= 0) return setValidation('Largura e altura precisam ser maiores que zero.')
    if (form.quantity < 1) return setValidation('Quantidade deve ser pelo menos 1.')
    if (isPhysicalWindow && form.closure_mode === 'MAÇANETA COM CHAVE E CREMONA') return setValidation('Folha de janela não recebe maçaneta com chave.')
    if (usesCremona && !form.cremona_description) return setValidation('Selecione a cremona deste orçamento.')
    if (needsGlass && !form.glass_description) return setValidation('Selecione ou cadastre o vidro.')
    if (customGlass && (!form.custom_glass_code || form.custom_glass_unit_price == null || !form.custom_glass_thickness_mm)) return setValidation('Vidro personalizado exige código, preço por m² e espessura.')
    if (form.panel_mode === 'SUPERIOR VIDRO/INFERIOR PAINEL' && !form.mixed_split_from_bottom_mm) return setValidation('Informe a altura da divisão do modo misto.')
    if (usesWindowLock && !form.window_lock_length_mm) return setValidation('Informe o comprimento da fechadura de janela.')
    if (form.shutter && form.panel_mode !== 'VIDRO INTEIRO') return setValidation('Persiana GR exige preenchimento VIDRO INTEIRO.')
    if (form.shutter?.mode === 'MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES' && form.leaf_count !== 2) return setValidation('Persiana em 2 painéis com eixos independentes exige GR de 2 folhas.')
    setValidation('')
    onSave({
      ...form,
      family: 'GR',
      id: item?.id || crypto.randomUUID(),
      cremona_description: usesCremona ? form.cremona_description : null,
      window_lock_length_mm: usesWindowLock ? form.window_lock_length_mm : null,
      mixed_split_from_bottom_mm: form.panel_mode === 'SUPERIOR VIDRO/INFERIOR PAINEL' ? form.mixed_split_from_bottom_mm : null,
      glass_description: needsGlass ? form.glass_description : null,
      custom_glass_code: needsGlass && customGlass ? form.custom_glass_code : null,
      custom_glass_unit_price: needsGlass && customGlass ? form.custom_glass_unit_price : null,
      custom_glass_thickness_mm: needsGlass && customGlass ? form.custom_glass_thickness_mm : null,
      bottom_flag_vertical_transoms: form.bottom_flag_height_mm ? form.bottom_flag_vertical_transoms : 0,
      top_flag_vertical_transoms: form.top_flag_height_mm ? form.top_flag_vertical_transoms : 0,
    })
  }
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form className="modal modal-large" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <div><strong>{item ? 'Editar Modelo Giro GR' : 'Inserir Modelo Giro GR'}</strong><span>Fase 25 final · GR_ENGINE_0.25.0</span></div>
          <button type="button" onClick={onClose}>×</button>
        </div>
        <div className="modal-scroll">
          {validation && <div className="error-banner compact">⚠ {validation}</div>}
          <FieldSection title="Medidas e sistema">
            <label>Largura (mm)<input type="number" min="1" value={form.width_mm} onChange={set('width_mm')} /></label>
            <label>Altura (mm)<input type="number" min="1" value={form.height_mm} onChange={set('height_mm')} /></label>
            <label>Quantidade<input type="number" min="1" value={form.quantity} onChange={set('quantity')} /></label>
            <label>Folhas<select value={form.leaf_count} onChange={set('leaf_count')}>{options.leaf_counts.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label className="span-2">Tipo físico da folha<select value={form.leaf_system} onChange={set('leaf_system')}>{options.leaf_systems.map((row) => <option key={row.value} value={row.value}>{row.label}</option>)}</select></label>
            <label>Aplicação comercial<select value={form.application} onChange={set('application')}>{options.applications.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Preenchimento<select value={form.panel_mode} onChange={set('panel_mode')}>{options.panel_modes.map((value) => <option key={value}>{value}</option>)}</select></label>
            {form.panel_mode === 'SUPERIOR VIDRO/INFERIOR PAINEL' && <label>Divisão desde a base (mm)<input type="number" min="1" value={form.mixed_split_from_bottom_mm || ''} onChange={set('mixed_split_from_bottom_mm')} /></label>}
          </FieldSection>
          <FieldSection title="Vidro">
            <label className="span-2">Vidro<select value={customGlass ? '__CUSTOM__' : (form.glass_description || '')} onChange={setCatalogGlass}><option value="">Sem vidro na folha</option>{options.glasses.map((glass) => <option key={`${glass.code || ''}-${glass.description}`} value={glass.description}>{glass.description}{glass.price != null ? ` · ${money(glass.price)}/m²` : ''}</option>)}<option value="__CUSTOM__">Outro vidro / preço manual…</option></select></label>
            {customGlass && <label className="span-2">Descrição<input value={form.glass_description || ''} onChange={set('glass_description')} /></label>}
            {customGlass && <label>Código<input value={form.custom_glass_code || ''} onChange={set('custom_glass_code')} /></label>}
            {customGlass && <label>Preço por m²<input type="number" min="0" step="0.01" value={form.custom_glass_unit_price ?? ''} onChange={set('custom_glass_unit_price')} /></label>}
            {customGlass && <label>Espessura (mm)<input type="number" min="0.1" max="34.9" step="0.1" value={form.custom_glass_thickness_mm ?? ''} onChange={set('custom_glass_thickness_mm')} /></label>}
            <label className="checkbox-row"><input type="checkbox" checked={form.screen_enabled} onChange={set('screen_enabled')} /> Tela recolhível TL3</label>
          </FieldSection>
          <FieldSection title="Bandeiras integradas">
            <label>Altura inferior (mm)<input type="number" min="0" value={form.bottom_flag_height_mm || 0} onChange={set('bottom_flag_height_mm')} /></label>
            <label>Divisões verticais inferiores<input type="number" min="0" value={form.bottom_flag_vertical_transoms || 0} onChange={set('bottom_flag_vertical_transoms')} /></label>
            <label>Altura superior (mm)<input type="number" min="0" value={form.top_flag_height_mm || 0} onChange={set('top_flag_height_mm')} /></label>
            <label>Divisões verticais superiores<input type="number" min="0" value={form.top_flag_vertical_transoms || 0} onChange={set('top_flag_vertical_transoms')} /></label>
            <div className="info-note">A ORCS GR não possui divisões horizontais de bandeira; a migração mantém apenas a matriz comprovada.</div>
          </FieldSection>
          <FieldSection title="Fechamento e ferragens">
            <label className="span-2">Fechamento<select value={form.closure_mode} onChange={set('closure_mode')}>{closureOptions.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Dobradiça<select value={form.hinge_description} onChange={set('hinge_description')}>{options.hinges.map((value) => <option key={value}>{value}</option>)}</select></label>
            {usesCremona && <label>Cremona<select value={form.cremona_description || ''} onChange={set('cremona_description')}><option value="">Selecione</option>{cremonaOptions.map((value) => <option key={value}>{value}</option>)}</select></label>}
            {usesWindowLock && <label>Comprimento da fechadura (mm)<input type="number" min="1" value={form.window_lock_length_mm || ''} onChange={set('window_lock_length_mm')} /></label>}
            {usesWindowLock && <div className="info-note">Fechadura de janela sem chave e sem cilindro. O comprimento é escolhido para cada orçamento.</div>}
          </FieldSection>
          <FieldSection title="Persiana">
            <label className="span-2">Modo<select value={form.shutter?.mode || 'SEM PERSIANA'} onChange={setShutter}><option>SEM PERSIANA</option>{(options.shutter?.modes || []).map((value) => <option key={value}>{value}</option>)}</select></label>
          </FieldSection>
        </div>
        <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary" type="submit">{item ? 'Salvar e recalcular' : 'Adicionar e recalcular'}</button></div>
      </form>
    </div>
  )
}

function AddItemModal({ onClose, onSave, options, item }) {
  const [form, setForm] = useState(() => ({
    ...baseDefaults,
    width_mm: 1200,
    height_mm: 1200,
    leaf_system: 'PRIME_WINDOW_42x66',
    glass_description: '04mm FLOAT INCOLOR',
    ...(item || {}),
    // Itens salvos pela API <= 0.4 podem ter apenas o booleano. Mantemos
    // ``null`` nesse caso para não inventar um modo de acionamento.
    shutter: item?.shutter || (item?.shutter_enabled ? null : baseDefaults.shutter),
    leaf_grid: item?.leaf_grid || baseDefaults.leaf_grid,
  }))
  const [validation, setValidation] = useState('')

  const set = (key) => (event) => {
    const target = event.target
    let value = target.type === 'checkbox' ? target.checked : target.value
    if (target.type === 'number' || key === 'leaf_count' || key === 'quantity') value = Number(value)
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const setGrid = (key) => (event) => {
    const value = Number(event.target.value)
    setForm((prev) => ({ ...prev, leaf_grid: { ...prev.leaf_grid, [key]: value } }))
  }

  const setShutter = (key) => (event) => {
    const value = event.target.value
    setForm((prev) => ({
      ...prev,
      shutter_enabled: false,
      shutter: { ...prev.shutter, [key]: value },
    }))
  }

  const togglePanel = (key) => (event) => setForm((prev) => ({
    ...prev,
    [key]: event.target.checked
      ? { height_mm: 400, horizontal_transoms: 0, vertical_transoms: 0 }
      : null,
  }))

  const setPanel = (key, field) => (event) => {
    const value = Number(event.target.value)
    setForm((prev) => ({ ...prev, [key]: { ...prev[key], [field]: value } }))
  }

  const setReinforcement = (event) => {
    const value = event.target.value
    setForm((prev) => ({
      ...prev,
      structural_reinforcement: value ? { material_code: value } : null,
    }))
  }

  const submit = (event) => {
    event.preventDefault()
    if (form.width_mm <= 0 || form.height_mm <= 0) return setValidation('Largura e altura precisam ser maiores que zero.')
    if (form.quantity < 1) return setValidation('Quantidade deve ser pelo menos 1.')
    setValidation('')
    onSave({ ...form, id: item?.id || crypto.randomUUID() })
  }

  const shutterActive = form.shutter?.mode && form.shutter.mode !== 'SEM PERSIANA'

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
            <label className="span-2">Persiana<select value={form.shutter?.mode || 'SEM PERSIANA'} onChange={setShutter('mode')}>{options.shutter.modes.map((value) => <option key={value}>{value}</option>)}</select></label>
            {shutterActive && <label>Caixa<select value={form.shutter.box_description} onChange={setShutter('box_description')}>{options.shutter.boxes.map((value) => <option key={value}>{value}</option>)}</select></label>}
            {shutterActive && <label>Tala<select value={form.shutter.slat_description} onChange={setShutter('slat_description')}>{options.shutter.slats.map((value) => <option key={value}>{value}</option>)}</select></label>}
            {shutterActive && <div className="info-note">Kit completo homologado: caixa, talas, guias, eixo, acessórios e acionamento são calculados pela Engine.</div>}
          </FieldSection>

          <FieldSection title="Travessas e bandeiras">
            <label>Travessas horizontais<input type="number" min="0" value={form.leaf_grid.horizontal_transoms} onChange={setGrid('horizontal_transoms')} /></label>
            <label>Travessas verticais<input type="number" min="0" value={form.leaf_grid.vertical_transoms} onChange={setGrid('vertical_transoms')} /></label>
            <label className="toggle-field"><span>Bandeira inferior</span><input type="checkbox" checked={Boolean(form.bottom_fixed_panel)} onChange={togglePanel('bottom_fixed_panel')} /></label>
            <label className="toggle-field"><span>Bandeira superior</span><input type="checkbox" checked={Boolean(form.top_fixed_panel)} onChange={togglePanel('top_fixed_panel')} /></label>
            {form.bottom_fixed_panel && <label>Altura inferior (mm)<input type="number" min="1" value={form.bottom_fixed_panel.height_mm} onChange={setPanel('bottom_fixed_panel', 'height_mm')} /></label>}
            {form.bottom_fixed_panel && <label>Travessas H/V inferior<div className="inline-inputs"><input type="number" min="0" value={form.bottom_fixed_panel.horizontal_transoms} onChange={setPanel('bottom_fixed_panel', 'horizontal_transoms')} /><input type="number" min="0" value={form.bottom_fixed_panel.vertical_transoms} onChange={setPanel('bottom_fixed_panel', 'vertical_transoms')} /></div></label>}
            {form.top_fixed_panel && <label>Altura superior (mm)<input type="number" min="1" value={form.top_fixed_panel.height_mm} onChange={setPanel('top_fixed_panel', 'height_mm')} /></label>}
            {form.top_fixed_panel && <label>Travessas H/V superior<div className="inline-inputs"><input type="number" min="0" value={form.top_fixed_panel.horizontal_transoms} onChange={setPanel('top_fixed_panel', 'horizontal_transoms')} /><input type="number" min="0" value={form.top_fixed_panel.vertical_transoms} onChange={setPanel('top_fixed_panel', 'vertical_transoms')} /></div></label>}
            <label className="span-2">Reforço estrutural<select value={form.structural_reinforcement?.material_code || ''} onChange={setReinforcement}><option value="">Sem reforço</option><option value="ALUM10238">ALUM10238</option><option value="ALUM15338">ALUM15338</option></select></label>
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
  const [modalFamily, setModalFamily] = useState('CR')
  const [editingItem, setEditingItem] = useState(null)
  const [options, setOptions] = useState(fallbackOptions)
  const [maximArOptions, setMaximArOptions] = useState(fallbackMaximArOptions)
  const [grOptions, setGrOptions] = useState(fallbackGrOptions)

  useEffect(() => { localStorage.setItem('software-esquadrias-items', JSON.stringify(items)) }, [items])
  useEffect(() => { localStorage.setItem('software-esquadrias-quote', JSON.stringify(quote)) }, [quote])

  const loadOptions = async () => {
    try {
      const [crResponse, maximArResponse, grResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/engine/cr/options`),
        fetch(`${API_URL}/api/v1/engine/maxim-ar/options`),
        fetch(`${API_URL}/api/v1/engine/gr/options`),
      ])
      if (!crResponse.ok || !maximArResponse.ok || !grResponse.ok) throw new Error('Falha ao carregar opções')
      setOptions(await crResponse.json())
      setMaximArOptions(await maximArResponse.json())
      setGrOptions(await grResponse.json())
    } catch {
      setOptions(fallbackOptions)
      setMaximArOptions(fallbackMaximArOptions)
      setGrOptions(fallbackGrOptions)
    }
  }

  const calculate = async (nextItems = items) => {
    if (!nextItems.length) { setData(null); return }
    setLoading(true); setError('')
    try {
      const payload = { items: nextItems.map(({ id, ...item }) => ({ ...item, family: item.family || 'CR' })) }
      const response = await fetch(`${API_URL}/api/v1/purchase-plans/calculate-all`, {
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

  const openNewCR = () => { setEditingItem(null); setModalFamily('CR'); setModalOpen(true) }
  const openNewMaximAr = () => { setEditingItem(null); setModalFamily('MAXIM_AR'); setModalOpen(true) }
  const openNewGr = () => { setEditingItem(null); setModalFamily('GR'); setModalOpen(true) }
  const openEdit = (item) => { setEditingItem(item); setModalFamily(item.family || 'CR'); setModalOpen(true) }

  const resetBaseline = () => {
    setItems(initialItems); calculate(initialItems)
  }

  return (
    <div className="app-shell">
      <Sidebar onAddCR={openNewCR} onAddMaximAr={openNewMaximAr} onAddGr={openNewGr} />
      <div className="workspace">
        <Header apiOnline={apiOnline} />
        <main className="content">
          <div className="page-head"><div><span className="eyebrow">ORÇAMENTO</span><h1>Novo Cliente / Orçamento</h1><p>Monte o pedido, calcule custos técnicos e gere o plano de compra.</p></div><div className="page-actions"><button className="secondary" onClick={resetBaseline}>Restaurar teste validado</button><button className="primary" onClick={() => calculate()} disabled={loading}>{loading ? 'Calculando...' : '↻ Recalcular pedido'}</button></div></div>
          {error && <div className="error-banner">⚠ {error}</div>}
          <div className="dashboard-grid">
            <div className="main-column">
              <ClientCard quote={quote} setQuote={setQuote} />
              <ItemsTable items={items} onRemove={removeItem} onAddCR={openNewCR} onAddMaximAr={openNewMaximAr} onAddGr={openNewGr} onEdit={openEdit} />
              <Analysis data={data} activeTab={activeTab} setActiveTab={setActiveTab} />
            </div>
            <Summary data={data} margin={margin} setMargin={setMargin} />
          </div>
        </main>
      </div>
      {modalOpen && (modalFamily === 'MAXIM_AR'
        ? <MaximArModal onClose={() => { setModalOpen(false); setEditingItem(null) }} onSave={saveItem} options={maximArOptions} item={editingItem} />
        : modalFamily === 'GR'
          ? <GrModal onClose={() => { setModalOpen(false); setEditingItem(null) }} onSave={saveItem} options={grOptions} item={editingItem} />
          : <AddItemModal onClose={() => { setModalOpen(false); setEditingItem(null) }} onSave={saveItem} options={options} item={editingItem} />)}
    </div>
  )
}
