import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

// Full Chromium's headless mode includes the native PDF viewer. The minimal
// headless shell cannot exercise PDF tabs; keep the existing FX suite intact.
test.use({ channel: 'chromium' })

const fixtures = JSON.parse(fs.readFileSync(fileURLToPath(new URL('../../api/tests/fixtures/op_reference_inputs.json', import.meta.url)), 'utf8')).cases
const registered = ['OP-GOLDEN-01', 'OP-GOLDEN-08', 'OP-GOLDEN-03'].map((id) => {
  const item = fixtures.find((entry) => entry.id === id)
  return { id: `ui-${item.technical_input.family}`, ...item.technical_input }
})
registered.push({ id: 'ui-FX', family: 'FX', width_mm: 1200, height_mm: 1000, quantity: 2,
  vertical_transoms: 0, horizontal_transoms: 0, glass_description: '04mm FLOAT INCOLOR',
  internal_finish: 'GUARNIÇÃO DE 70MM', external_finish: 'BARRA CHATA DE 30MM' })
const quote = { client: 'CLIENTE TESTE C', clientCode: 'CLI-C', project: 'OBRA TESTE C', workCode: 'OBR-C',
  number: 'CONF-FASE-C', phone: '', city: '', date: '2026-11-05', notes: '' }
const panel = (page) => page.locator('.op-card')
const generateButton = (page) => panel(page).getByRole('button', { name: 'Gerar OP de Conferência', exact: true })
const isPdf = (response) => response.url().endsWith('/api/v1/production-orders/pdf') && response.request().method() === 'POST'

function decodePdf(content) {
  const code = "import sys,json,pymupdf; d=pymupdf.open(stream=sys.stdin.buffer.read(),filetype='pdf'); print(json.dumps({'pages':len(d),'text':'\\n'.join(p.get_text() for p in d),'images':sum(len(p.get_images()) for p in d)}))"
  return JSON.parse(execFileSync(process.env.E2E_PYTHON || 'python', ['-c', code], { input: content, encoding: 'utf8' }))
}

async function openOrder(page, items = registered, { finish = 'BRANCO' } = {}) {
  await page.addInitScript(({ items, quote, finish }) => {
    if (sessionStorage.getItem('op-test-seeded')) return
    sessionStorage.setItem('op-test-seeded', 'true')
    localStorage.setItem('software-esquadrias-items', JSON.stringify(items))
    localStorage.setItem('software-esquadrias-quote', JSON.stringify(quote))
    localStorage.setItem('software-esquadrias-op-items:00000000-0000-0000-0000-000000000001',
      JSON.stringify(Object.fromEntries(items.map((item, index) => [item.id, { label: `C-${index + 1}`, finishKey: finish }]))))
  }, { items, quote, finish })
  await page.goto('/')
  await expect(page.getByRole('status')).toHaveText('API online')
}

async function generate(page) {
  const response = page.waitForResponse(isPdf)
  await generateButton(page).click()
  const pdf = await response
  expect(pdf.status()).toBe(200)
  await expect(panel(page).getByRole('link', { name: 'Baixar PDF' })).toBeVisible()
  // Inspect the exact Blob offered to the user, independently of DevTools'
  // network-body retention for no-store PDF responses and embedded viewers.
  const bytes = await page.evaluate(async () => {
    const url = document.querySelector('.op-file-actions a[download]').href
    return Array.from(new Uint8Array(await (await fetch(url)).arrayBuffer()))
  })
  expect(bytes.length).toBeGreaterThan(1000)
  return { response: pdf, decoded: decodePdf(Buffer.from(bytes)) }
}

for (const item of registered) {
  test(`OP ${item.family}: readiness, PDF real, cabeçalho e uma entrada sem multiplicar quantidade`, async ({ page }) => {
    await openOrder(page, [item])
    const sequence = []
    page.on('request', (request) => {
      if (/\/production-orders\/(pdf-readiness|pdf)$/.test(request.url())) sequence.push(request)
    })
    const { response, decoded } = await generate(page)
    expect(sequence.map((request) => request.url().split('/').pop())).toEqual(['pdf-readiness', 'pdf'])
    expect(sequence[0].postDataJSON()).toEqual(response.request().postDataJSON().layout_request)
    const sent = response.request().postDataJSON()
    expect(sent.purpose).toBe('REVIEW')
    expect(sent.layout_request.production_order.items).toHaveLength(1)
    expect(sent.layout_request.production_order.items[0].technical_input).toEqual((({ id, ...input }) => input)(item))
    expect(decoded.pages).toBeGreaterThanOrEqual(2)
    for (const value of ['CONFERÊNCIA', 'NÃO FABRICAR', 'CLIENTE TESTE C', 'CLI-C', 'OBRA TESTE C', 'OBR-C', 'C-1', String(item.width_mm)]) expect(decoded.text).toContain(value)
    expect(response.headers()['x-op-fabrication-allowed']).toBe('false')
    if (process.env.OP_IMAGE_MANIFEST) {
      expect(decoded.images).toBeGreaterThan(0)
      expect(decoded.text).not.toContain('Croqui não disponível')
    }
    await expect(panel(page).getByText('A OP aguarda auditoria independente e conferência visual.', { exact: false })).toBeVisible()
    await expect(panel(page).locator('iframe')).toHaveCount(0)
    await expect(panel(page).getByText('PDF gerado', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: /emitir.*definitiva|fabricar/i })).toHaveCount(0)
  })
}

test('pedido misto inclui os quatro modelos; seleção parcial e individual não duplicam quantidades', async ({ page }) => {
  await openOrder(page)
  const first = await generate(page)
  const sent = first.response.request().postDataJSON().layout_request.production_order.items
  expect(sent.map((item) => item.technical_input.family)).toEqual(['CR', 'MAXIM_AR', 'GR', 'FX'])
  expect(sent.map((item) => item.technical_input.quantity)).toEqual(registered.map((item) => item.quantity))
  for (const label of ['C-1', 'C-2', 'C-3', 'C-4']) expect(first.decoded.text).toContain(label)
  await panel(page).getByLabel('Incluir item 02', { exact: false }).uncheck()
  await panel(page).getByLabel('Incluir item 03', { exact: false }).uncheck()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  const second = await generate(page)
  expect(second.response.request().postDataJSON().layout_request.production_order.items.map((item) => item.item_id)).toEqual(['ui-CR', 'ui-FX'])
  expect(second.decoded.text).not.toContain('Item C-2')
  await panel(page).getByLabel('Incluir item 01', { exact: false }).uncheck()
  expect((await generate(page)).response.request().postDataJSON().layout_request.production_order.items).toHaveLength(1)
  await panel(page).getByRole('button', { name: 'Limpar seleção', exact: true }).click()
  await expect(generateButton(page)).toBeDisabled()
  await panel(page).getByRole('button', { name: 'Selecionar todos', exact: true }).click()
  await expect(panel(page).getByText('4 de 4 itens selecionados')).toBeVisible()
})

test('PDF abre em outra aba e pode ser salvo como arquivo PDF íntegro', async ({ page }) => {
  await openOrder(page, [registered[3]])
  const generated = await generate(page)
  const popupPromise = page.waitForEvent('popup')
  await panel(page).getByRole('link', { name: 'Visualizar PDF', exact: true }).click()
  const popup = await popupPromise
  await expect.poll(() => popup.url()).toMatch(/^blob:/)
  await popup.close()
  const downloadPromise = page.waitForEvent('download')
  await panel(page).getByRole('link', { name: 'Baixar PDF', exact: true }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('ordem-producao-conferencia.pdf')
  const target = test.info().outputPath('op-conferencia.pdf')
  await download.saveAs(target)
  const content = fs.readFileSync(target)
  expect(content.subarray(0, 5).toString()).toBe('%PDF-')
  expect(decodePdf(content)).toEqual(generated.decoded)
})

test('editar dimensão e quantidade invalida PDF e solicita dados novos sem multiplicar itens', async ({ page }) => {
  await openOrder(page, [registered[3]])
  const first = await generate(page)
  await page.locator('.items-card').getByTitle('Editar', { exact: true }).click()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  await page.locator('form').getByLabel('Largura (mm)', { exact: true }).fill('1537')
  await page.locator('form').getByLabel('Quantidade', { exact: true }).fill('3')
  await page.locator('form button[type=submit]').click()
  const second = await generate(page)
  const sent = second.response.request().postDataJSON().layout_request.production_order.items
  expect(sent).toHaveLength(1)
  expect(sent[0].technical_input.width_mm).toBe(1537)
  expect(sent[0].technical_input.quantity).toBe(3)
  expect(second.decoded.text).toContain('1537')
  expect(second.response.headers()['x-op-snapshot-sha256']).not.toBe(first.response.headers()['x-op-snapshot-sha256'])
})

test('cabeçalho, identificação e cor invalidam PDF e aproveitam os campos existentes', async ({ page }) => {
  await openOrder(page, [registered[3]])
  await generate(page)
  await page.getByLabel('Cliente *', { exact: true }).fill('CLIENTE ATUALIZADO')
  await page.getByLabel('Código do cliente', { exact: true }).fill('CLI-NOVO')
  await page.getByLabel('Código da obra', { exact: true }).fill('OBR-NOVA')
  await page.getByLabel('Obra', { exact: true }).fill('OBRA ATUALIZADA')
  await panel(page).getByLabel('Identificação do item 01', { exact: true }).fill('SALA-FIXO')
  await panel(page).getByRole('group', { name: 'Cor do croqui do item 01' }).getByRole('button', { name: 'Preto' }).click()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  const result = await generate(page)
  for (const value of ['CLIENTE ATUALIZADO', 'CLI-NOVO', 'OBR-NOVA', 'OBRA ATUALIZADA', 'SALA-FIXO']) expect(result.decoded.text).toContain(value)
  expect(result.response.request().postDataJSON().layout_request.production_order.items[0].finish_key).toBe('PRETO')
  await expect(panel(page).getByRole('group', { name: 'Cor do croqui do item 01' }).getByRole('button', { name: 'Preto' })).toHaveAttribute('aria-pressed', 'true')
  const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('software-esquadrias-quote')))
  expect(saved.clientCode).toBe('CLI-NOVO')
  expect(saved.workCode).toBe('OBR-NOVA')
  await page.reload()
  await expect(page.getByLabel('Código do cliente', { exact: true })).toHaveValue('CLI-NOVO')
  await expect(panel(page).getByLabel('Identificação do item 01', { exact: true })).toHaveValue('SALA-FIXO')
  await expect(panel(page).getByRole('link')).toHaveCount(0) // PDF bytes/URLs are not persisted.
})

test('dados técnicos incompletos ou rejeitados pela Engine não geram PDF', async ({ page }) => {
  await openOrder(page, [{ ...registered[3], width_mm: 0 }])
  let pdfCalls = 0
  page.on('request', (request) => { if (request.url().endsWith('/production-orders/pdf')) pdfCalls++ })
  await generateButton(page).click()
  await expect(panel(page).getByRole('alert')).toContainText('medidas positivas')
  await page.locator('.items-card').getByTitle('Editar', { exact: true }).click()
  await page.locator('form').getByLabel('Largura (mm)', { exact: true }).fill('150')
  await page.locator('form').getByLabel('Travessas verticais', { exact: true }).fill('2')
  await page.locator('form button[type=submit]').click()
  await generateButton(page).click()
  await expect(panel(page).getByRole('alert')).toContainText('HTTP 422')
  await expect(panel(page).getByRole('alert')).toContainText('Geometria FX inválida')
  expect(pdfCalls).toBe(0)
})

test('API indisponível informa erro e não disponibiliza links antigos', async ({ page }) => {
  await openOrder(page, [registered[3]])
  await generate(page)
  await page.route('**/api/v1/production-orders/pdf-readiness', (route) => route.abort('connectionrefused'))
  await generateButton(page).click()
  await expect(panel(page).getByRole('alert')).toContainText('API indisponível')
  await expect(panel(page).getByRole('link')).toHaveCount(0)
})

test('saúde offline desabilita geração e explica como retomar', async ({ page }) => {
  await page.route('**/health', (route) => route.abort('connectionrefused'))
  await page.addInitScript(() => localStorage.setItem('software-esquadrias-items', '[]'))
  await page.goto('/')
  await expect(page.getByRole('status')).toHaveText('API offline')
  await expect(generateButton(page)).toBeDisabled()
  await expect(panel(page).getByRole('alert')).toContainText('Ligue o servidor')
})

test('resposta atrasada não restaura PDF antigo depois de alteração do pedido', async ({ page }) => {
  await openOrder(page, [registered[3]])
  let release, captured, delivered
  const gate = new Promise((resolve) => { release = resolve })
  const received = new Promise((resolve) => { captured = resolve })
  const completed = new Promise((resolve) => { delivered = resolve })
  await page.route('**/api/v1/production-orders/pdf', async (route) => {
    const response = await route.fetch()
    captured()
    await gate
    await route.fulfill({ response }).catch(() => {}) // Request can be aborted by the edit.
    delivered()
  })
  await generateButton(page).click()
  await received
  await page.getByLabel('Obra', { exact: true }).fill('OBRA MAIS NOVA')
  release()
  await completed
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  await expect(generateButton(page)).toBeEnabled()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  await expect(panel(page).getByText('O pedido ou a seleção mudou.', { exact: false })).toBeVisible()
  await page.unroute('**/api/v1/production-orders/pdf')
  const result = await generate(page)
  expect(result.decoded.text).toContain('OBRA MAIS NOVA')
})

test('cancelamento conserva seleção e não dispara PDF após readiness atrasado', async ({ page }) => {
  await openOrder(page, [registered[3]])
  let release, captured, delivered
  const gate = new Promise((resolve) => { release = resolve })
  const received = new Promise((resolve) => { captured = resolve })
  const completed = new Promise((resolve) => { delivered = resolve })
  let pdfCalls = 0
  page.on('request', (request) => { if (request.url().endsWith('/production-orders/pdf')) pdfCalls++ })
  await page.route('**/api/v1/production-orders/pdf-readiness', async (route) => {
    const response = await route.fetch()
    captured()
    await gate
    await route.fulfill({ response }).catch(() => {})
    delivered()
  })
  await generateButton(page).click()
  await received
  await panel(page).getByRole('button', { name: 'Cancelar geração', exact: true }).click()
  release()
  await completed
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  await expect(panel(page).getByText('Geração cancelada.', { exact: false })).toBeVisible()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  await expect(panel(page).getByText('1 de 1 itens selecionados')).toBeVisible()
  expect(pdfCalls).toBe(0)
})

test('OP em celular mantém seleção, botão e download acessíveis', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await openOrder(page, [registered[3]])
  const { decoded } = await generate(page)
  expect(decoded.text).toContain('CONFERÊNCIA')
  const bounds = await panel(page).boundingBox()
  expect(bounds.x).toBeGreaterThanOrEqual(0)
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390)
  await expect(panel(page).getByRole('link', { name: 'Baixar PDF', exact: true })).toBeVisible()
  await page.screenshot({ path: test.info().outputPath('op-mobile.png') })
})

// Empty OP color metadata must not cause missing technical data from a blank finish.
test('cor branca ja vem selecionada e pode ser alternada pelo seletor dividido', async ({ page }) => {
  await page.addInitScript(({ items, quote }) => {
    localStorage.setItem('software-esquadrias-items', JSON.stringify(items))
    localStorage.setItem('software-esquadrias-quote', JSON.stringify(quote))
    localStorage.removeItem('software-esquadrias-op-items:00000000-0000-0000-0000-000000000001')
  }, { items: [registered[3]], quote })
  await page.goto('/')
  await expect(page.getByRole('status')).toHaveText('API online')
  const group = panel(page).getByRole('group', { name: 'Cor do croqui do item 01' })
  await expect(group.getByRole('button', { name: 'Branco' })).toHaveAttribute('aria-pressed', 'true')
  const first = await generate(page)
  expect(first.response.request().postDataJSON().layout_request.production_order.items[0].finish_key).toBe('BRANCO')
  await group.getByRole('button', { name: 'Preto' }).click()
  await expect(panel(page).getByRole('link')).toHaveCount(0)
  await expect(group.getByRole('button', { name: 'Preto' })).toHaveAttribute('aria-pressed', 'true')
  const second = await generate(page)
  expect(second.response.request().postDataJSON().layout_request.production_order.items[0].finish_key).toBe('PRETO')
})
