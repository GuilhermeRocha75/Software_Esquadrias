import { test, expect } from '@playwright/test'

test('home separa áreas, mantém cadastro e abre os quatro modelos', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('navigation', { name: 'Áreas do software' }).getByRole('button')).toHaveCount(4)
  await expect(page.locator('.client-card')).toHaveCount(0)
  await expect(page.locator('.items-card')).toHaveCount(0)
  await expect(page.locator('.analysis-card')).toHaveCount(0)
  await page.getByRole('button', { name: /^Cadastro de Cliente/ }).click()
  await page.getByLabel('Cliente *', { exact: true }).fill('Cliente da interface')
  await page.getByRole('button', { name: /Continuar para itens/ }).click()
  await expect(page.locator('.analysis-card')).toBeVisible()
  for (const name of ['+ Inserir Fixo', '+ Inserir Giro GR', '+ Inserir Maxim-Ar', '＋ Inserir Modelo Correr']) {
    await page.getByRole('button', { name, exact: true }).click()
    await expect(page.locator('form')).toBeVisible()
    await page.getByRole('button', { name: 'Cancelar', exact: true }).click()
  }
  for (const name of ['Custo por Grupo', 'BOM / Consumo', 'Compra de Barras', 'Plano de Corte', 'Alertas']) {
    await page.locator('.tabs').getByRole('button', { name, exact: false }).click()
    await expect(page.locator('.tabs button.active')).toContainText(name)
  }
  await page.getByRole('button', { name: /Voltar ao início/ }).click()
  await page.reload()
  await page.getByRole('button', { name: /^Cadastro de Cliente/ }).click()
  await expect(page.getByLabel('Cliente *', { exact: true })).toHaveValue('Cliente da interface')
})

for (const width of [1440, 390]) {
  test(`home em ${width}px mantém navegação e resumo sem rolagem horizontal`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/')
    await expect(page.locator('.home-summary')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    await page.screenshot({ path: test.info().outputPath(`home-${width}.png`), fullPage: true })
  })
}
