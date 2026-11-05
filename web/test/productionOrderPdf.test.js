import assert from 'node:assert/strict'
import test from 'node:test'
import { fetchProductionOrderReview } from '../src/productionOrderPdf.js'

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
