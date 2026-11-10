import test from 'node:test'
import assert from 'node:assert/strict'
import { calculateQuote } from '../src/commercialQuote.js'

const item = { id: 'cr', quantity: 2, width_mm: 1200, height_mm: 1500 }
const costs = [{ unit_technical_cost: 200.00001 }]
test('custo da engine, fator, quantidade e instalação do resumo', () => {
  const quote = calculateQuote([item], costs, { factor: '2', perArea: '100', perUnit: '25', fixed: '50' })
  assert.deepEqual([quote.area, quote.subtotal, quote.installation, quote.total], [3.6, 800, 460, 1260])
})
test('custo manual substitui a base antes da margem individual', () => {
  const quote = calculateQuote([item], costs, { factor: '2', lines: { cr: { cost: '100', factor: '1.5' } } })
  assert.equal(quote.subtotal, 300)
})
test('leitura monetária do VBA e ausência de custo calculado', () => {
  assert.equal(calculateQuote([item], [{ unit_technical_cost: 100.12346 }]).rows[0].unit, 100.1235)
  assert.equal(calculateQuote([item], [{}]), null)
})
