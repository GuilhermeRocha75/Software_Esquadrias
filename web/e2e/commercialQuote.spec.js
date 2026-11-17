import { test, expect } from '@playwright/test'

test('edição comercial no orçamento completo persiste e atualiza o PDF', async ({ page }) => {
  await page.addInitScript(() => {
    if (sessionStorage.getItem('commercial-seeded')) return
    sessionStorage.setItem('commercial-seeded', 'true')
    localStorage.setItem('software-esquadrias-items', JSON.stringify([
      { id: 'commercial-fx', family: 'FX', width_mm: 1200, height_mm: 1000, quantity: 2,
        vertical_transoms: 0, horizontal_transoms: 0, glass_description: '04mm FLOAT INCOLOR',
        internal_finish: 'GUARNIÇÃO DE 70MM', external_finish: 'BARRA CHATA DE 30MM' },
    ]))
    localStorage.setItem('software-esquadrias-quote', JSON.stringify({ client: 'Teste comercial', number: '001', date: '2026-11-16' }))
  })
  await page.goto('/')
  await expect(page.locator('.home-summary .summary-line').first()).not.toContainText('—')
  await expect(page.locator('#orcamento-comercial')).toHaveCount(0)
  await page.getByRole('button', { name: /^Orçamentos/ }).click()
  const dialog = page.getByRole('dialog')
  for (const [label, value] of [['Fator de margem geral', '2'], ['Instalação (R$/m²)', '10'],
    ['Instalação (R$/unidade)', '5'], ['Instalação fixa (R$)', '50'], ['Custo manual do item 1', '100']]) {
    await dialog.getByLabel(label, { exact: true }).fill(value)
  }
  await expect(dialog.locator('.sale-price strong')).toHaveText(/484,00/)
  await dialog.getByRole('button', { name: 'Fechar', exact: true }).click()
  await page.reload()
  await expect(page.locator('.home-summary .summary-line').first()).not.toContainText('—')
  await expect(page.locator('#orcamento-comercial')).toHaveCount(0)
  for (const name of [/^Orçamentos/]) {
    await page.getByRole('button', { name, exact: false }).click()
    await expect(dialog.getByLabel('Fator de margem geral', { exact: true })).toHaveValue('2')
    await expect(dialog.getByLabel('Custo manual do item 1', { exact: true })).toHaveValue('100')
    await expect(dialog.locator('.sale-price strong')).toHaveText(/484,00/)
    await dialog.getByRole('button', { name: 'Fechar', exact: true }).click()
  }
  await page.getByRole('button', { name: /^Orçamentos/ }).click()
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/quotes/full-pdf') && r.request().method() === 'POST')
  await dialog.getByRole('button', { name: 'Gerar PDF do orçamento', exact: true }).click()
  const pdf = await response
  expect(pdf.status()).toBe(200)
  expect(pdf.request().postDataJSON().installation).toBe(84)
  expect(pdf.request().postDataJSON().lines[0]).toMatchObject({ unit: 200, total: 400 })
  await expect(dialog.getByRole('link', { name: 'Baixar PDF', exact: true })).toBeVisible()
  await page.screenshot({ path: test.info().outputPath('orcamento-completo.png') })
})
