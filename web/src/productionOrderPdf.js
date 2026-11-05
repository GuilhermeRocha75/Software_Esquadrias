// Integração de conferência; a interface de emissão para fabricação segue fechada.
export async function fetchProductionOrderReview(apiUrl, layoutRequest, {
  fetchImpl = globalThis.fetch, signal,
} = {}) {
  const response = await fetchImpl(`${apiUrl.replace(/\/+$/, '')}/api/v1/production-orders/pdf`, {
    method: 'POST', cache: 'no-store', signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ layout_request: layoutRequest, purpose: 'REVIEW' }),
  })
  if (!response.ok) throw new Error(`PDF de conferência indisponível (HTTP ${response.status}).`)
  if (!response.headers.get('Content-Type')?.startsWith('application/pdf') ||
      response.headers.get('X-OP-Mode') !== 'REVIEW' ||
      response.headers.get('X-OP-Fabrication-Allowed') !== 'false') {
    throw new Error('Resposta sem identificação segura de conferência.')
  }
  const blockingCount = Number(response.headers.get('X-OP-Blocking-Count'))
  const pages = Number(response.headers.get('X-OP-Pages'))
  const snapshotSha256 = response.headers.get('X-OP-Snapshot-SHA256')
  if (!Number.isInteger(blockingCount) || blockingCount < 1 || !Number.isInteger(pages) || pages < 1 ||
      !/^[0-9a-f]{64}$/.test(snapshotSha256 || '')) throw new Error('Metadados da conferência inválidos.')
  const blob = await response.blob()
  if (await blob.slice(0, 5).text() !== '%PDF-') throw new Error('Conteúdo recebido não é um PDF.')
  return {
    blob, fabricationAllowed: false, blockingCount, pages, snapshotSha256,
    filename: 'ordem-producao-conferencia.pdf',
  }
}
