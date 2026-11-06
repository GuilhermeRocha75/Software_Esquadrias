import assert from 'node:assert/strict'
import test from 'node:test'
import { buildProductionLayoutRequest, DEMO_COMPANY_ID, explainProductionBlocker } from '../src/productionOrderRequest.js'

const quote = { client: 'CLIENTE DE TESTE', clientCode: 'C01', project: 'OBRA DE TESTE', workCode: 'O01', number: 'CONF-01', notes: 'não encaminhar' }
const items = ['CR', 'MAXIM_AR', 'GR', 'FX'].map((family, index) => ({ id: `item-${index + 1}`, family,
  width_mm: 1200 + index, height_mm: 1000, quantity: index + 1, internal_finish: 'GUARNIÇÃO DE 70MM',
  ...(['CR', 'MAXIM_AR'].includes(family) ? { leaf_grid: { horizontal_transoms: 1, vertical_transoms: 0, custom_dimensions: [{ axis: 'X', index: 0, clear_span_mm: 300 }] } } : {}),
}))

test('pedido misto preserva uma entrada por item, quantidade e todos os parâmetros aninhados', () => {
  const request = buildProductionLayoutRequest(items, quote, items.map((item) => item.id))
  assert.equal(request.production_order.items.length, 4)
  items.forEach(({ id, ...technical }, index) => {
    assert.deepEqual(request.production_order.items[index].technical_input, technical)
    assert.equal(request.production_order.items[index].item_id, id)
    assert.equal(request.production_order.items[index].finish_key, null)
  })
  assert.equal(request.context.company_id, DEMO_COMPANY_ID)
  assert.equal(request.production_order.company_id, request.context.company_id)
  assert.deepEqual(request.context.item_labels.map((item) => item.label), ['01', '02', '03', '04'])
})

test('seleção individual ou parcial mantém a ordem cadastrada sem duplicar produtos', () => {
  const partial = buildProductionLayoutRequest(items, quote, ['item-4', 'item-2'])
  assert.deepEqual(partial.production_order.items.map((item) => item.item_id), ['item-2', 'item-4'])
  assert.deepEqual(partial.production_order.items.map((item) => item.technical_input.quantity), [2, 4])
  const single = buildProductionLayoutRequest(items, quote, ['item-4'])
  assert.equal(single.production_order.items.length, 1)
  assert.equal(single.context.item_labels[0].label, '04')
})

test('cabeçalho aproveita cadastro e metadata não entra na engenharia nem presume cor branca', () => {
  const request = buildProductionLayoutRequest(items, quote, ['item-1'], { 'item-1': { label: ' JANELA SALA ', finishKey: ' PRETO ' } })
  assert.equal(request.production_order.items[0].finish_key, 'PRETO')
  assert.equal(request.context.item_labels[0].label, 'JANELA SALA')
  assert.equal(request.context.client_name, quote.client)
  assert.equal(request.context.client_code, 'C01')
  assert.equal(request.context.work_name, quote.project)
  assert.equal(request.context.work_code, 'O01')
  assert.ok(!JSON.stringify(request).includes('não encaminhar'))
  assert.deepEqual(request.production_order.items[0].technical_input, (({ id, ...input }) => input)(items[0]))
  const empty = buildProductionLayoutRequest(items, {}, ['item-1'])
  assert.equal(empty.context.client_name, null)
  assert.equal(empty.context.work_name, null)
})

test('snapshot não compartilha dados mutáveis e cadastro CR anterior continua aceito', () => {
  const copy = structuredClone(items)
  delete copy[0].family
  const request = buildProductionLayoutRequest(copy, quote, ['item-1'])
  copy[0].leaf_grid.custom_dimensions[0].clear_span_mm = 999
  assert.equal(request.production_order.items[0].technical_input.leaf_grid.custom_dimensions[0].clear_span_mm, 300)
  assert.equal(request.production_order.items[0].technical_input.family, 'CR')
  assert.equal(copy[0].family, undefined)
})

test('seleção vazia, IDs duplicados, desconhecidos e identificações repetidas são recusados', () => {
  for (const selected of [[], ['item-1', 'item-1'], ['missing']]) assert.throws(() => buildProductionLayoutRequest(items, quote, selected))
  assert.throws(() => buildProductionLayoutRequest([items[0], items[0]], quote, ['item-1']))
  assert.throws(() => buildProductionLayoutRequest(items, quote, ['item-1', 'item-2'], { 'item-1': { label: 'J1' }, 'item-2': { label: 'J1' } }), /identificações diferentes/)
  assert.throws(() => buildProductionLayoutRequest(items, quote, ['item-1'], {}, 'unknown'), /Empresa/)
})

test('medidas ausentes, quantidade fracionária, modelo inválido e NaN aninhado não são corrigidos silenciosamente', () => {
  for (const changes of [{ width_mm: '' }, { height_mm: -1 }, { quantity: 2.5 }, { quantity: true }, { family: 'PV' },
    { leaf_grid: { custom_dimensions: [{ clear_span_mm: NaN }] } }]) {
    assert.throws(() => buildProductionLayoutRequest([{ ...items[0], ...changes }], quote, ['item-1']))
  }
})

test('pendências conhecidas têm explicação e mensagens técnicas desconhecidas são preservadas', () => {
  assert.match(explainProductionBlocker({ code: 'MISSING_ASSET' }), /Imagem não importada/)
  assert.match(explainProductionBlocker({ code: 'INDEPENDENT_DOCUMENT_AUDIT_PENDING' }), /Não está liberada/)
  assert.equal(explainProductionBlocker({ code: 'FRACTIONAL', message: 'Quantidade 12,835714285714285 pendente' }), 'Quantidade 12,835714285714285 pendente')
})
