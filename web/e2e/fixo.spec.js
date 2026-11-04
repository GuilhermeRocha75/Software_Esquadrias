import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../..', import.meta.url))
const evidence = JSON.parse(fs.readFileSync(path.join(root,
  'engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/test_cases/fixo_validation_v0_1.json'), 'utf8'))
const cases = evidence.manual_cases
const money = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
const total = (page) => page.locator('.summary-line').filter({ hasText: 'Custo técnico' }).locator('strong')
const fxRow = (page) => page.locator('.items-card tbody tr').filter({ hasText: 'Painel Fixo' })
const isCalculation = (response) => response.url().endsWith('/api/v1/purchase-plans/calculate-all') && response.request().method() === 'POST'

async function fillFixo(page, cfg) {
  const form = page.locator('form')
  for (const [label, key] of Object.entries({ 'Largura (mm)': 'width_mm', 'Altura (mm)': 'height_mm',
    Quantidade: 'quantity', 'Travessas verticais': 'vertical_transoms', 'Travessas horizontais': 'horizontal_transoms' })) {
    await form.getByLabel(label, { exact: true }).fill(String(cfg[key]))
  }
  await form.getByRole('combobox', { name: 'Vidro', exact: true }).selectOption(cfg.glass_description)
  await form.getByLabel('Acabamento interno').selectOption(cfg.internal_finish)
  await form.getByLabel('Acabamento externo').selectOption(cfg.external_finish)
}

async function saveFixo(page) {
  const response = page.waitForResponse(isCalculation)
  await page.locator('form button[type=submit]').click()
  return await response
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (localStorage.getItem('software-esquadrias-items') === null) localStorage.setItem('software-esquadrias-items', '[]')
  })
  await page.goto('/')
  await expect(page.getByRole('status')).toHaveText('API online')
})

for (const item of cases) {
  test(`FX ${item.name}: interface, API real e valores da planilha`, async ({ page }) => {
    await page.getByRole('button', { name: 'Inserir Modelo Fixo', exact: false }).click()
    await fillFixo(page, item.configuration)
    if (item.name === 'SIMPLES') await page.screenshot({ path: test.info().outputPath('fixo-desktop.png') })
    const response = await saveFixo(page)
    expect(response.status()).toBe(200)
    const calculated = (await response.json()).items[0]
    expect(calculated.unit_technical_cost).toBeCloseTo(item.expected.unit_technical_cost, 7)
    expect(calculated.geometry.glass_width_mm).toBeCloseTo(item.expected.glass_width_mm, 7)
    expect(calculated.geometry.glass_height_mm).toBeCloseTo(item.expected.glass_height_mm, 7)
    expect(calculated.geometry.glass_quantity).toBe(item.expected.glass_quantity_per_product)
    await expect(total(page)).toHaveText(money(item.expected.order_technical_cost))
    await expect(fxRow(page)).toContainText('Calculado')
    await page.getByRole('button', { name: 'BOM / Consumo', exact: true }).click()
    const code = calculated.bom.find((component) => component.source === 'FX!27').material_code
    const glassRow = page.locator('.analysis-card tbody tr').filter({ hasText: code })
    await expect(glassRow.locator('td').nth(4)).toHaveText(
      new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(item.expected.glass_quantity_order))
    await page.getByRole('button', { name: 'Plano de Corte', exact: true }).click()
    await expect(page.locator('.cut-material').first()).toBeVisible()
    await expect(page.locator('.error-banner')).toHaveCount(0)
  })
}

test('editar, persistir e remover um Fixo mantém orçamento e disponibilidade coerentes', async ({ page }) => {
  await page.getByRole('button', { name: 'Inserir Modelo Fixo', exact: false }).click()
  await fillFixo(page, cases[0].configuration)
  expect((await saveFixo(page)).status()).toBe(200)
  await expect(total(page)).toHaveText(money(cases[0].expected.order_technical_cost))
  await fxRow(page).getByTitle('Editar', { exact: true }).click()
  await fillFixo(page, cases[1].configuration)
  expect((await saveFixo(page)).status()).toBe(200)
  await expect(fxRow(page)).toHaveCount(1)
  await expect(total(page)).toHaveText(money(cases[1].expected.order_technical_cost))
  await page.reload()
  await expect(total(page)).toHaveText(money(cases[1].expected.order_technical_cost))
  await fxRow(page).getByTitle('Editar', { exact: true }).click()
  await expect(page.getByLabel('Travessas horizontais', { exact: true })).toHaveValue('3')
  await expect(page.getByLabel('Quantidade', { exact: true })).toHaveValue('2')
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click()
  await fxRow(page).getByTitle('Excluir', { exact: true }).click()
  await expect(fxRow(page)).toHaveCount(0)
  await expect(total(page)).toHaveText(money(0))
  await expect(page.getByRole('status')).toHaveText('API online')
})

test('geometria impossível retorna 422, não exibe Calculado e permite corrigir o item', async ({ page }) => {
  await page.getByRole('button', { name: 'Inserir Modelo Fixo', exact: false }).click()
  await fillFixo(page, { ...cases[0].configuration, width_mm: 150, vertical_transoms: 2 })
  expect((await saveFixo(page)).status()).toBe(422)
  await expect(fxRow(page)).toContainText('Não calculado')
  await expect(page.locator('.error-banner')).toContainText('Geometria FX inválida')
  await expect(total(page)).toHaveText(money(0))
  await expect(page.getByRole('status')).toHaveText('API online')
  await fxRow(page).getByTitle('Editar', { exact: true }).click()
  await fillFixo(page, cases[0].configuration)
  expect((await saveFixo(page)).status()).toBe(200)
  await expect(total(page)).toHaveText(money(cases[0].expected.order_technical_cost))
  await expect(page.locator('.error-banner')).toHaveCount(0)
})

test('resposta de um cálculo antigo não sobrescreve o item recém-editado', async ({ page }) => {
  let release
  let firstReady
  let count = 0
  const delayed = new Promise((resolve) => { release = resolve })
  const ready = new Promise((resolve) => { firstReady = resolve })
  await page.route('**/api/v1/purchase-plans/calculate-all', async (route) => {
    if (++count === 1) {
      const response = await route.fetch()
      firstReady()
      await delayed
      await route.fulfill({ response })
    } else await route.continue()
  })
  await page.getByRole('button', { name: 'Inserir Modelo Fixo', exact: false }).click()
  await fillFixo(page, cases[0].configuration)
  await page.locator('form button[type=submit]').click()
  await ready
  await expect(fxRow(page)).toContainText('Não calculado')
  await fxRow(page).getByTitle('Editar', { exact: true }).click()
  await fillFixo(page, cases[1].configuration)
  expect((await saveFixo(page)).status()).toBe(200)
  await expect(total(page)).toHaveText(money(cases[1].expected.order_technical_cost))
  const oldResponse = page.waitForResponse((response) => isCalculation(response) &&
    response.request().postDataJSON().items[0].width_mm === cases[0].configuration.width_mm)
  release()
  await (await oldResponse).finished()
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  await expect(total(page)).toHaveText(money(cases[1].expected.order_technical_cost))
})

test('configurador Fixo permite inclusão em tela de celular', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: '+ Inserir Fixo', exact: true }).click()
  await fillFixo(page, cases[0].configuration)
  const bounds = await page.locator('form').boundingBox()
  expect(bounds.x).toBeGreaterThanOrEqual(0)
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390)
  await expect(page.locator('form button[type=submit]')).toBeVisible()
  await page.screenshot({ path: test.info().outputPath('fixo-mobile.png') })
  expect((await saveFixo(page)).status()).toBe(200)
  await expect(total(page)).toHaveText(money(cases[0].expected.order_technical_cost))
})


test('Fixo maior que a barra mantém peça integral e permite divisão pela fabricação', async ({ page }) => {
  await page.getByRole('button', { name: 'Inserir Modelo Fixo', exact: false }).click()
  await fillFixo(page, { ...cases[0].configuration, width_mm: 7500, height_mm: 2500, vertical_transoms: 3, quantity: 2 })
  const response = await saveFixo(page)
  expect(response.status()).toBe(200)
  const result = await response.json()
  const expected = await page.request.post('/api/v1/engine/fixo/calculate', { data: {
    family: 'FX', width_mm: 7500, height_mm: 2500, vertical_transoms: 3, quantity: 2,
  } })
  expect(expected.status()).toBe(200)
  expect(result.items[0].order_technical_cost).toBe((await expected.json()).order_technical_cost)
  await expect(fxRow(page)).toContainText('Calculado')
  await expect(page.locator('.error-banner')).toHaveCount(0)
  await page.getByRole('button', { name: 'Plano de Corte', exact: true }).click()
  await expect(page.locator('.cut-label').filter({ hasText: 'divisão e emenda pela fabricação' }).first()).toBeVisible()
  await expect(page.locator('.cut-pieces').filter({ hasText: '7.505 mm' }).first()).toBeVisible()
  await page.screenshot({ path: test.info().outputPath('fixo-emenda.png') })
})
