import assert from 'node:assert/strict'
import test from 'node:test'
import { fetchProductionOrderReview, generateProductionOrderReview } from '../src/productionOrderPdf.js'

function pdfResponse(overrides = {}) {
  const headers = new Map(Object.entries({
    'Content-Type': 'application/pdf', 'X-OP-Mode': 'REVIEW',
    'X-OP-Fabrication-Allowed': 'false', 'X-OP-Blocking-Count': '4',
    'X-OP-Pages': '2', 'X-OP-Snapshot-SHA256': 'a'.repeat(64), ...overrides,
  }))
  return { ok: true, headers: { get: (key) => headers.get(key) }, blob: async () => new Blob(['%PDF-test']) }
}

test('PDF usa somente modo REVIEW, sem cache ou emissão automática', async () => {
  let request
  const layout = { production_order: { order_id: 'ANON' }, context: {} }
  const result = await fetchProductionOrderReview('https://example.invalid/', layout, {
    fetchImpl: async (url, options) => { request = { url, options }; return pdfResponse() },
  })
  assert.equal(request.url, 'https://example.invalid/api/v1/production-orders/pdf')
  assert.equal(request.options.cache, 'no-store')
  assert.deepEqual(JSON.parse(request.options.body), { layout_request: layout, purpose: 'REVIEW' })
  assert.equal(result.fabricationAllowed, false)
  assert.equal(result.blockingCount, 4)
  assert.equal(result.pages, 2)
  assert.equal(result.filename, 'ordem-producao-conferencia.pdf')
})

test('PDF recusa HTML, modo produtivo e resposta sem bloqueio explícito', async () => {
  for (const headers of [
    { 'Content-Type': 'text/html' }, { 'X-OP-Mode': 'PRODUCTION' },
    { 'X-OP-Fabrication-Allowed': 'true' }, { 'X-OP-Fabrication-Allowed': null },
  ]) await assert.rejects(fetchProductionOrderReview('', {}, { fetchImpl: async () => pdfResponse(headers) }))
})

test('PDF propaga cancelamento e informa falha HTTP sem tratar JSON como PDF', async () => {
  const controller = new AbortController()
  await assert.rejects(fetchProductionOrderReview('', {}, {
    signal: controller.signal,
    fetchImpl: async (_, options) => { assert.equal(options.signal, controller.signal); return { ok: false, status: 409 } },
  }), /HTTP 409/)
})

test('PDF recusa metadados incompletos e conteúdo HTML com MIME incorreto', async () => {
  for (const headers of [
    { 'X-OP-Pages': '0' }, { 'X-OP-Blocking-Count': null }, { 'X-OP-Snapshot-SHA256': 'wrong' },
  ]) await assert.rejects(fetchProductionOrderReview('', {}, { fetchImpl: async () => pdfResponse(headers) }))
  const response = pdfResponse()
  response.blob = async () => new Blob(['<html>fallback</html>'])
  await assert.rejects(fetchProductionOrderReview('', {}, { fetchImpl: async () => response }), /não é um PDF/)
})

const ready = () => ({ review_allowed: true, fabrication_allowed: false, layout_sha256: 'a'.repeat(64),
  blockers: [{ code: 'INDEPENDENT_DOCUMENT_AUDIT_PENDING', message: 'Auditoria pendente.' }] })
const jsonResponse = (value) => ({ ok: true, headers: new Headers({ 'Content-Type': 'application/json' }), json: async () => value })

test('fluxo consulta readiness primeiro e encaminha o mesmo snapshot, somente REVIEW', async () => {
  const calls = []
  const layout = { production_order: { items: [{ technical_input: { width_mm: 1200, quantity: 2 } }] }, context: {} }
  const original = structuredClone(layout)
  const result = await generateProductionOrderReview('', layout, {
    fetchImpl: async (url, request) => {
      calls.push({ url, request })
      return calls.length === 1 ? jsonResponse(ready()) : pdfResponse()
    },
    onReadiness: () => { layout.production_order.items[0].technical_input.width_mm = 9999 },
  })
  assert.ok(calls[0].url.endsWith('/pdf-readiness'))
  assert.deepEqual(JSON.parse(calls[0].request.body), original)
  assert.deepEqual(JSON.parse(calls[1].request.body), { layout_request: original, purpose: 'REVIEW' })
  assert.ok(calls.every((call) => call.request.cache === 'no-store'))
  assert.equal(result.readiness.fabrication_allowed, false)
})

test('readiness inválido, HTML ou liberação de fabricação impedem solicitar PDF', async () => {
  for (const value of [
    { ...ready(), fabrication_allowed: true }, { ...ready(), review_allowed: false },
    { ...ready(), blockers: [] }, { ...ready(), layout_sha256: 'incorrect' },
    { ...ready(), blockers: [{ code: 'MISSING_ASSET' }] },
  ]) {
    let calls = 0
    await assert.rejects(generateProductionOrderReview('', {}, { fetchImpl: async () => { calls++; return jsonResponse(value) } }))
    assert.equal(calls, 1)
  }
  await assert.rejects(generateProductionOrderReview('', {}, {
    fetchImpl: async () => ({ ok: true, headers: new Headers({ 'Content-Type': 'text/html' }) }),
  }), /não retornou as pendências/)
})

test('cancelamento após readiness não dispara renderização e hash diferente invalida o PDF', async () => {
  const controller = new AbortController()
  let calls = 0
  await assert.rejects(generateProductionOrderReview('', {}, {
    signal: controller.signal, onReadiness: () => controller.abort(),
    fetchImpl: async () => { calls++; return jsonResponse(ready()) },
  }), { name: 'AbortError' })
  assert.equal(calls, 1)
  calls = 0
  await assert.rejects(generateProductionOrderReview('', {}, {
    fetchImpl: async () => ++calls === 1 ? jsonResponse(ready()) : pdfResponse({ 'X-OP-Snapshot-SHA256': 'b'.repeat(64) }),
  }), /mudaram durante a geração/)
})

test('erros de rede, schema e armazenamento possuem explicações sem objeto serializado', async () => {
  await assert.rejects(generateProductionOrderReview('', {}, { fetchImpl: async () => { throw new TypeError('Failed to fetch') } }), /API indisponível/)
  await assert.rejects(generateProductionOrderReview('', {}, { fetchImpl: async () => ({ ok: false, status: 422,
    json: async () => ({ detail: [{ loc: ['body', 'production_order', 'items', 0, 'width_mm'], msg: 'Field required' }] }),
  }) }), /Revise os dados técnicos.*width_mm: Field required/)
  await assert.rejects(generateProductionOrderReview('', {}, { fetchImpl: async () => ({ ok: false, status: 503,
    json: async () => ({ detail: 'Armazenamento indisponível' }),
  }) }), /serviço de imagens está indisponível/)
})
