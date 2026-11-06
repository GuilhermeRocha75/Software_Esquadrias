// Contrato B1 a partir dos itens cadastrados. Nenhum cálculo de engenharia.
export const DEMO_COMPANY_ID = '00000000-0000-0000-0000-000000000001'
export const OP_PROFILE_COLORS = ['BRANCO', 'PRETO']
export function selectedProfileColor(value) {
  const color = String(value ?? '').trim().toUpperCase()
  return OP_PROFILE_COLORS.includes(color) ? color : 'BRANCO'
}

export function buildProductionLayoutRequest(items, quote, selectedIds, metadata = {}, companyId = DEMO_COMPANY_ID) {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(companyId)) throw new Error('Empresa da OP não configurada corretamente.')
  if (!items.length || !selectedIds.length) throw new Error('Selecione ao menos um item cadastrado para gerar a OP.')
  const ids = items.map((item) => item.id)
  if (ids.some((id) => typeof id !== 'string' || !id.trim()) || new Set(ids).size !== ids.length ||
      new Set(selectedIds).size !== selectedIds.length || selectedIds.some((id) => !ids.includes(id))) throw new Error('A identificação dos itens é inválida ou duplicada. Revise o pedido.')
  const selected = items.filter((item) => selectedIds.includes(item.id))
  const optional = (value) => String(value ?? '').trim() || null
  const labels = selected.map((item) => ({ item_id: item.id, label: optional(metadata[item.id]?.label) || String(ids.indexOf(item.id) + 1).padStart(2, '0') }))
  if (new Set(labels.map((entry) => entry.label)).size !== labels.length) throw new Error('Use identificações diferentes para os itens selecionados.')
  function finite(node) {
    if (typeof node === 'number' && !Number.isFinite(node)) throw new Error('Há um valor técnico não numérico. Revise as configurações do item.')
    if (node && typeof node === 'object') Object.values(node).forEach(finite)
  }
  const entries = selected.map((item) => {
    const { id, finish_key, ...technical } = item
    const label = labels.find((entry) => entry.item_id === id).label
    technical.family = technical.family || 'CR' // Compatibilidade do cadastro anterior.
    if (!['CR', 'MAXIM_AR', 'GR', 'FX'].includes(technical.family)) throw new Error(`Item ${label}: modelo não suportado na OP de conferência.`)
    if (![technical.width_mm, technical.height_mm].every((value) => Number.isFinite(value) && value > 0) ||
        !Number.isInteger(technical.quantity) || technical.quantity < 1) throw new Error(`Item ${label}: informe medidas positivas e quantidade inteira no cadastro da esquadria.`)
    finite(technical)
    return { item_id: id, finish_key: selectedProfileColor(metadata[id]?.finishKey || finish_key), technical_input: structuredClone(technical) }
  })
  return {
    production_order: { company_id: companyId, order_id: optional(quote.number) || 'CONFERENCIA', items: entries },
    context: { company_id: companyId, client_code: optional(quote.clientCode), client_name: optional(quote.client),
      work_code: optional(quote.workCode), work_name: optional(quote.project), item_labels: labels },
  }
}

const explanations = {
  INDEPENDENT_DOCUMENT_AUDIT_PENDING: 'A OP aguarda auditoria independente e conferência visual. Não está liberada para fabricar.',
  MISSING_ASSET: 'Imagem não importada para este modelo, perfil ou cor. O PDF será gerado com a ausência indicada.',
  INVALID_ASSET: 'Uma imagem não passou na verificação. Confira a biblioteca privada na API.',
  MISSING_OR_INVALID_PDF_ASSET: 'Imagem indisponível ou inválida. Nenhum desenho substituto será usado.',
  MISSING_HEADER_DATA: 'Confira Código do cliente, Cliente e Obra no cabeçalho do orçamento; há dados ausentes.',
  FRACTIONAL_UNIT_REVIEW: 'Há quantidade fracionária cuja unidade física precisa de confirmação. O valor original foi preservado sem arredondamento.',
  MISSING_TECHNICAL_DATA: 'Faltam dados para identificar uma imagem ou uma informação técnica. Confira o cadastro e a cor do croqui.',
  CONSUMPTION_PRESENTATION_REVIEW: 'A unidade de consumo precisa de conferência; não deve ser interpretada como quantidade de peças.',
  DYNAMIC_LAYOUT_REVIEW: 'Este modelo tem divisões que exigem conferência da apresentação.',
  UNMAPPED_LEGACY_ROW: 'Há uma linha técnica adicional cuja posição no documento original precisa ser confirmada.',
}

export function explainProductionBlocker(blocker) {
  return explanations[blocker.code] || blocker.message
}
